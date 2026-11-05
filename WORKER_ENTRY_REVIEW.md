# WORKER ENTRY INDEPENDENT REVIEW

Base42b7711ea6af2b9802eff60715e5fe002e525d5d.
Fresh separate reviewer worker_entry_review, source-only, one requested whole-change review.
No reviewer OS/native/security experiments or edits.

## Important/P2: W birth observation erased

entry_peer returned40 when run_worker had succeeded but a later P/channel/final ACK failed.
main mapped all non0/41 statuses to worker_started=false. Unknown/killed E status also implied false.
New final_ack and unknown_owner_exit regression cases both RED, then GREEN after repair.
Successful W birth now survives later failures as exit41/true; unknown E status is null.
An original pidfd set before an ambiguous creation return is also preserved as birth evidence.
The reviewer reread this production repair, but relied on coordinator test execution.

## Minor/P3: test recv-error wrapper examined untouched ancillary storage

__wrap_recvmsg inspected msg_control even after real recvmsg=-1.
New recv_error_probe constructed a canary credential buffer with EBADF:
RED showed buffer modification; early n<0 return made it GREEN.
This final test-only repair was author-verified after reviewer completion.

## Evidence limits retained

Negative cases principally assert fail-closed JSON plus selected FD/wait counters.
They do not prove all negative-path FD leaks absent or arbitrary descendant drain.
A new E→W cancelled-return case complements the earlier F→E cancellation case and confirms
original pidfd wait plus monotonic birth reporting for this fixed fixture.
No protected factory/code origin, real cross-UID seal, systemd/cgroup authority or qualification evidence.
All58 frozen files matched the base in independent source review.

No other Important/Critical finding identified by this review.
No whole-final-tree independent C0/I0 certification; final test-only changes receive author regression.

## Reviewed production SHA256 (unchanged after review)

~~~text
3a39ddd4539e2bd3cbe78b1a9e237414c9d5a959fdd9f5462b6037e01b448241  research/worker_entry/integration.c
2462b5cfc2f7d76b473f29fec184154941d1a19ec30b06f75c29ee02c69dfe03  research/worker_entry/fixed_worker.c
a2655d57466afae8438d87077cd60b0c5fa8ab8a498a4ff116efa7f38dab621a  research/worker_entry/entry_credential.c
4599ce0d2832e4801fc82befd444357c998d2b51bcd31c6bc728d836c2121089  research/worker_entry/entry_credential.h
~~~

Rulings: preserve historical evidence and unknown residue; no code/OS authority promotion.
Return after final report/local commit, do not start forbidden privileged lab or remote publication.
