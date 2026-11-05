/* Fixed NORMAL synthetic M/credential boundary for the real-kernel lab.
 * No runtime fault selector, FS/clone/kill interposition or actual UID/cap changes.
 * M remains synthetic even though the external user unit and D are real. */
const char *fm_test_case="normal";
const char *entry_case="normal";
