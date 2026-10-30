"""Pure independent causal ledger for the declared stopped-task capture profile."""

from dataclasses import dataclass, field

from .contracts import Capture, CaptureAssessment, TraceEvent

NATIVE_ARCH = 0xC000003E
EXIT_CALLS = {60, 231}
FORK_CALLS = {56, 57, 58, 435}
FD_RETURNS = {
    2,
    22,
    32,
    33,
    41,
    43,
    53,
    85,
    213,
    253,
    257,
    282,
    283,
    284,
    288,
    289,
    290,
    291,
    292,
    293,
    294,
    298,
    300,
    319,
    323,
    425,
    428,
    430,
    432,
    433,
    434,
    437,
    438,
    444,
}
BPF_FD_COMMANDS = {0, 5, 7, 13, 14, 17, 18, 19, 28, 30, 32, 33}


@dataclass
class Task:
    tid: int
    image: int = 0
    pending: tuple[int, ...] | None = None
    last: tuple[int, ...] | None = None
    fds: dict[int, tuple[int, ...]] = field(default_factory=dict)
    initialized: bool = False
    expected_snapshot: bool = False
    dead: bool = False
    pre_exit: int | None = None
    seed_allowed: bool = True
    after_exec: bool = False
    inherited: dict[int, tuple[int, ...]] | None = None
    inherited_origins: dict[int, tuple[int, ...]] = field(default_factory=dict)
    origins: dict[int, tuple[int, ...]] = field(default_factory=dict)


@dataclass
class Call:
    task: int
    nr: int
    args: tuple[int, ...]
    fds: dict[int, tuple[int, ...]]
    origins: dict[int, tuple[int, ...]]
    result: int | None = None
    aborted: bool = False
    after: dict[int, tuple[int, ...]] | None = None


def needs_snapshot(nr: int, args: tuple[int, ...], result: int) -> bool:
    if result < 0:
        return False
    return (
        nr in FD_RETURNS
        or nr in {3, 436}
        or (nr == 72 and args[1] in {0, 2, 1030})
        or (nr == 317 and args[1] & 8 != 0)
        or (nr == 321 and args[0] in BPF_FD_COMMANDS)
    )


def evaluate_capture(capture: Capture) -> CaptureAssessment:
    capture.__post_init__()
    tasks: dict[int, Task] = {}
    reasons: list[str] = []
    pairs = aborts = execs = changes = notifications = donations = 0
    seen_calls: set[int] = set()
    calls: dict[int, Call] = {}
    typed_receipts: list[tuple[TraceEvent, tuple[int, int] | None]] = []
    clock = 0
    root_status = None

    def reject(reason: str) -> None:
        if reason not in reasons:
            reasons.append(reason)

    def fd_table(event: TraceEvent, state: Task) -> None:
        nonlocal changes
        call_id, count, *raw = event.values
        current = {raw[i]: tuple(raw[i + 1 : i + 6]) for i in range(0, count * 6, 6)}
        if not state.initialized:
            if call_id:
                reject("FD_INITIAL_TABLE_MISSING")
            if state.inherited is not None and current != state.inherited:
                reject("FD_INHERITANCE_MISMATCH")
            state.fds = current
            state.origins = {
                fd: state.inherited_origins.get(fd, (event.task, 0, fd)) for fd in current
            }
            state.initialized = True
            return
        previous = state.fds
        added = set(current) - set(previous)
        removed = set(previous) - set(current)
        changed = {fd for fd in set(current) & set(previous) if current[fd] != previous[fd]}
        if state.after_exec:
            if added or changed or removed != {fd for fd, v in previous.items() if v[0] & 0x80000}:
                reject("FD_EXEC_TABLE_MISMATCH")
            state.after_exec = False
        elif state.last is None or state.last[0] != call_id:
            if added or removed or changed:
                reject("FD_UNEXPLAINED_MUTATION")
        else:
            _, nr, *tail = state.last
            args = tuple(tail[:6])
            result = tail[6]
            scalar_fd = (
                nr in FD_RETURNS - {22, 53, 293}
                or nr == 321
                or nr == 317
                or (nr == 72 and args[1] in {0, 1030})
            )
            if scalar_fd and result >= 0:
                if result not in current or (result not in added and nr not in {33, 292}):
                    reject("FD_RETURN_MISMATCH")
                if (added - {result}) or (removed - {result}):
                    reject("FD_UNEXPLAINED_MUTATION")
            elif nr == 3 and result == 0:
                if args[0] not in previous or removed != {args[0]} or added or changed:
                    reject("FD_CLOSE_MISMATCH")
            elif nr == 436 and result == 0:
                if args[2] != 0:
                    reject("FD_CLOSE_RANGE_FLAGS_UNSUPPORTED")
                expected = {fd for fd in previous if args[0] <= fd <= args[1]}
                if removed != expected or added or changed:
                    reject("FD_CLOSE_RANGE_MISMATCH")
            elif nr in {22, 53, 293} and result == 0:
                if len(added) != 2 or removed or changed:
                    reject("FD_PAIR_ACQUISITION_MISMATCH")
            elif nr == 72 and args[1] == 2 and result == 0:
                if added or removed or changed - {args[0]}:
                    reject("FD_FLAG_UPDATE_MISMATCH")
            elif added or removed or changed:
                reject("FD_UNEXPLAINED_MUTATION")
        changes += len(added) + len(removed) + len(changed)
        for fd in removed:
            state.origins.pop(fd, None)
        for fd in added | changed:
            origin: tuple[int, ...] = (event.task, call_id, fd)
            call = calls.get(call_id)
            if call is not None:
                if call.nr in {32, 33, 292} or (call.nr == 72 and call.args[1] in {0, 1030}):
                    source = call.origins.get(call.args[0])
                    if source is None:
                        reject("FD_DUP_SOURCE_UNKNOWN")
                    else:
                        origin = source
                elif call.nr == 438:
                    pidfd = call.origins.get(call.args[0])
                    pidfd_call = calls.get(pidfd[1]) if pidfd is not None else None
                    target = next(
                        (
                            t
                            for t in tasks.values()
                            if pidfd_call is not None
                            and pidfd_call.nr == 434
                            and t.tid == pidfd_call.args[0]
                            and not t.dead
                        ),
                        None,
                    )
                    if target is None or call.args[1] not in target.origins:
                        reject("FD_PIDFD_SOURCE_UNKNOWN")
                    else:
                        origin = target.origins[call.args[1]]
            state.origins[fd] = origin
        state.fds = current
        if call_id in calls:
            calls[call_id].after = dict(current)
        state.expected_snapshot = False

    for expected, event in enumerate(capture.events, 1):
        if event.seq != expected:
            reject("SEQUENCE_MISMATCH")
        if event.mono_ns < clock:
            reject("CLOCK_ORDER_INVALID")
        clock = event.mono_ns
        if event.kind == "BIRTH":
            parent, flags = event.values
            if event.task in tasks or any(
                t.tid == event.tid and not t.dead for t in tasks.values()
            ):
                reject("TASK_IDENTITY_MISMATCH")
            if flags & 0x10400:
                reject("FD_SHARED_TABLE_UNSUPPORTED")
            if parent:
                parent_state = tasks.get(parent)
                if (
                    parent_state is None
                    or parent_state.dead
                    or parent_state.pending is None
                    or parent_state.pending[2] not in FORK_CALLS
                ):
                    reject("BIRTH_WITHOUT_PARENT_CALL")
            elif tasks:
                reject("MULTIPLE_CAPTURE_ROOTS")
            child = Task(event.tid)
            if parent and parent in tasks:
                child.inherited = dict(tasks[parent].fds)
                child.inherited_origins = dict(tasks[parent].origins)
            tasks[event.task] = child
            if event.image:
                reject("EXEC_GENERATION_MISMATCH")
            continue
        state = tasks.get(event.task)
        if state is None or state.dead or state.tid != event.tid:
            reject("TASK_IDENTITY_MISMATCH")
            continue
        expected_image = state.image + (event.kind == "EXEC")
        if event.image != expected_image:
            reject("EXEC_GENERATION_MISMATCH")
        values = event.values
        match event.kind:
            case "ENTER":
                if state.pending is not None:
                    reject("CALL_ALREADY_PENDING")
                if state.expected_snapshot or not state.initialized:
                    reject("FD_SNAPSHOT_MISSING")
                if values[0] in seen_calls or values[0] == 0:
                    reject("CALL_ID_MISMATCH")
                seen_calls.add(values[0])
                calls[values[0]] = Call(
                    event.task, values[2], values[3:], dict(state.fds), dict(state.origins)
                )
                if values[1] != NATIVE_ARCH:
                    reject("WRONG_SYSCALL_ABI")
                state.pending = values
                state.seed_allowed = False
            case "RETURN":
                call_id, result = values
                if call_id == 0 and result == 0 and state.seed_allowed and state.pending is None:
                    state.seed_allowed = False
                    continue
                if state.pending is None:
                    reject("CALL_WITHOUT_ENTRY")
                    continue
                pending = state.pending
                if call_id != pending[0]:
                    reject("CALL_ID_MISMATCH")
                state.last = (call_id, pending[2], *pending[3:], result)
                if call_id in calls:
                    calls[call_id].result = result
                state.expected_snapshot = needs_snapshot(pending[2], pending[3:], result)
                state.pending = None
                pairs += 1
            case "ABORT":
                if state.pending is None or values[0] != state.pending[0]:
                    reject("CALL_ID_MISMATCH")
                elif not values[1] and state.pending[2] not in EXIT_CALLS:
                    reject("UNJUSTIFIED_CALL_ABORT")
                state.pending = None
                aborts += 1
                if values[0] in calls:
                    calls[values[0]].aborted = True
            case "FDS":
                fd_table(event, state)
            case "EXEC":
                if state.pending is None or state.pending[2] not in {59, 322}:
                    reject("EXEC_WITHOUT_CALL")
                if values[0] != state.tid:
                    reject("FD_NONLEADER_EXEC_UNSUPPORTED")
                state.image += 1
                state.after_exec = True
                execs += 1
            case "PRE_EXIT":
                state.pre_exit = values[0]
            case "EXIT":
                if state.pending is not None:
                    reject("PENDING_CALL_AT_EXIT")
                if state.expected_snapshot:
                    reject("FD_SNAPSHOT_MISSING")
                if state.pre_exit is None or state.pre_exit != values[0]:
                    reject("EXIT_WITHOUT_PRE_EXIT")
                state.dead = True
                if event.task == 1:
                    root_status = values[0]
            case "ERROR":
                reject("COLLECTOR_ERROR")
            case "NOTIFY_RECV" | "ADDFD" | "NOTIFY_SEND":
                bindings = [
                    (generation, t.pending[0])
                    for generation, t in tasks.items()
                    if event.kind == "NOTIFY_RECV"
                    and t.tid == values[2]
                    and not t.dead
                    and t.pending is not None
                ]
                typed_receipts.append((event, bindings[0] if len(bindings) == 1 else None))
            case "SIGNAL":
                pass
    # Receipts may be scheduled after the target's syscall exit. Reconcile immutable
    # entry/snapshot histories, never whichever PID/FD happens to be current now.
    seen_receipts: set[int] = set()
    requests: dict[tuple[tuple[int, ...], int], tuple[int, int]] = {}
    deliveries: dict[int, tuple[int, tuple[int, ...]]] = {}
    replies: dict[int, tuple[int, int]] = {}
    for event, binding in typed_receipts:
        v = event.values
        call = calls.get(v[0])
        expected_ioctl = {
            "NOTIFY_RECV": 0xC0502100,
            "ADDFD": 0x40182103,
            "NOTIFY_SEND": 0xC0182101,
        }[event.kind]
        if (
            call is None
            or call.task != event.task
            or call.nr != 16
            or call.args[1] != expected_ioctl
            or call.result is None
            or v[0] in seen_receipts
        ):
            reject("FD_NOTIFICATION_RECEIPT_MISMATCH")
            continue
        seen_receipts.add(v[0])
        listener = call.origins.get(call.args[0])
        if listener is None:
            reject("FD_NOTIFICATION_LISTENER_UNKNOWN")
            continue
        key = (listener, v[1])
        if event.kind == "NOTIFY_RECV":
            notifications += 1
            if call.result != 0 or v[6] != call.args[0] or key in requests:
                reject("FD_NOTIFICATION_RECEIPT_MISMATCH")
            if not any(t.tid == v[2] for t in tasks.values()):
                reject("FD_NOTIFICATION_TARGET_UNKNOWN")
                continue
            if binding is None:
                reject("FD_NOTIFICATION_CALL_MISMATCH")
                continue
            target_call = calls[binding[1]]
            if v[5] != NATIVE_ARCH or target_call.nr != v[4] or target_call.args != v[7:]:
                reject("FD_NOTIFICATION_CALL_MISMATCH")
                continue
            requests[key] = binding
        elif event.kind == "ADDFD":
            if key not in requests:
                reject("FD_NOTIFICATION_ID_UNKNOWN")
                continue
            target_task, target_id = requests[key]
            target = calls[target_id]
            if v[6] != call.result:
                reject("FD_ADDFD_RESULT_MISMATCH")
            if v[2] != 2:
                reject("FD_ADDFD_NOT_ATOMIC_SEND")
            if call.result < 0:
                continue
            if target.aborted or (tasks[target_task].dead and target.result is None):
                reject("FD_ADDFD_TARGET_GONE")
            source = call.fds.get(v[3])
            if source is None:
                reject("FD_ADDFD_SOURCE_UNKNOWN")
                continue
            if source[0] & 3:
                reject("FD_ADDFD_NOT_READ_ONLY")
            if target_id in deliveries or target_id in replies:
                reject("FD_DUPLICATE_NOTIFICATION_REPLY")
            deliveries[target_id] = (call.result, source)
            donations += 1
        else:
            if key not in requests:
                reject("FD_NOTIFICATION_ID_UNKNOWN")
                continue
            if v[5] != call.result or v[4] != 0:
                reject("FD_NOTIFICATION_SEND_MISMATCH")
            if call.result == 0:
                target_id = requests[key][1]
                if target_id in replies or target_id in deliveries:
                    reject("FD_DUPLICATE_NOTIFICATION_REPLY")
                replies[target_id] = (v[2], v[3])
    for call_id, call in calls.items():
        if (
            call.nr == 16
            and call.result is not None
            and call.args[1] in {0xC0502100, 0x40182103, 0xC0182101}
            and (call.result >= 0 or call.args[1] != 0xC0502100)
            and call_id not in seen_receipts
        ):
            reject("FD_NOTIFICATION_RECEIPT_MISSING")
    for (listener, _), (_task_id, call_id) in requests.items():
        target = calls[call_id]
        if target.aborted:
            continue
        if call_id in deliveries:
            result, source = deliveries[call_id]
            actual = target.after.get(result) if target.after is not None else None
            if (
                target.result != result
                or actual is None
                or actual[1:] != source[1:]
                or actual[0] & 3
            ):
                reject("FD_ADDFD_RESULT_MISMATCH")
        elif call_id in replies:
            value, error = replies[call_id]
            if error >= 0 or not -4095 <= error < 0 or target.result != error:
                reject("FD_NOTIFICATION_SEND_MISMATCH")
        elif target.result == -38 and not any(
            listener in t.origins.values() for t in tasks.values() if not t.dead
        ):
            # Listener ENOSYS is observable, but never a process-termination verdict.
            pass
        else:
            reject("FD_NOTIFICATION_RECEIPT_MISSING")
    if any(not t.dead for t in tasks.values()):
        reject("TASK_NOT_REAPED")
    if capture.end_values != (len(capture.events), len(tasks), 0, root_status):
        reject("END_COUNTER_MISMATCH")
    if root_status != 0:
        reject("ROOT_EXIT_NONZERO")
    capture_complete = not any(not r.startswith("FD_") for r in reasons)
    return CaptureAssessment(
        capture_complete,
        capture_complete and not reasons,
        len(tasks),
        pairs,
        aborts,
        execs,
        changes,
        notifications,
        donations,
        tuple(reasons),
    )
