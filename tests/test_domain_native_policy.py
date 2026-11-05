"""Native helper fixtures use regular files, NOT kernel cgroups."""

import subprocess

import pytest

from native_e_lab.domain import _binary


@pytest.mark.parametrize(
    "case",
    [
        "scope",
        "original_replaced",
        "members",
        "empty",
        "descendants",
        "missing_stat",
        "kernel_schema",
        "oversize",
        "duplicate",
        "negative",
        "missing_dying",
    ],
)
def test_native_fail_closed_policy_on_private_regular_fixture(tmp_path, case):
    native = _binary().with_suffix(".c")
    # Test-only source entry rename; production contains no fixture/fault switch.
    copy = tmp_path / "instrumented.c"
    copy.write_text(
        native.read_text().replace(
            "int main(int argc, char **argv)", "int unused_domain_main(int argc, char **argv)"
        )
    )
    probe = tmp_path / "probe.c"
    probe.write_text(r"""
#include "instrumented.c"
int main(int argc,char **argv) {
 if(argc!=3)return 2;
 if(!strcmp(argv[1],"scope"))
  return !factory_service("/user.slice/native-e-domain-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.service") ||
   factory_service("/init.scope") || factory_service("/native-e-domain-x.service") ||
   factory_service("/native-e-domain-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.service/child");
 int parent=open(argv[2],O_DIRECTORY|O_RDONLY|O_CLOEXEC);
 if(parent<0 || mkdirat(parent,"D",0700))return 3;
 int d=openat(parent,"D",O_RDONLY|O_DIRECTORY|O_CLOEXEC),anchor=dup(d),bad=0;
 if(!strcmp(argv[1],"original_replaced")) {
  if(!original_D(parent,d,anchor,"D"))return 4;
  if(renameat(parent,"D",parent,"kept-original") || mkdirat(parent,"D",0700))return 5;
  bad=original_D(parent,d,anchor,"D");
 }else if(!strcmp(argv[1],"members")) {
  int f=openat(d,"cgroup.procs",O_WRONLY|O_CREAT|O_EXCL,0600);
  if(f<0 || write(f,"111\n222\n",8)!=8)return 6;close(f);
  bad=exactly_child(d,111);
 }else if(!strcmp(argv[1],"descendants")) {
  int f=openat(d,"cgroup.stat",O_WRONLY|O_CREAT|O_EXCL,0600);
  const char *text="nr_descendants 1\n" "nr_dying_descendants 0\n";
  if(f<0 || write(f,text,strlen(text))!=(ssize_t)strlen(text))return 6;close(f);
  bad=no_descendants(d);
 }else if(!strcmp(argv[1],"missing_stat")) {
  bad=no_descendants(d);
 }else if(!strcmp(argv[1],"kernel_schema") || !strcmp(argv[1],"oversize") ||
          !strcmp(argv[1],"duplicate") || !strcmp(argv[1],"negative") ||
          !strcmp(argv[1],"missing_dying")) {
  char text[6000];strcpy(text,"nr_descendants 0\n");
  if(!strcmp(argv[1],"negative"))strcpy(text,"nr_descendants -0\n");
  for(int i=0;i<18;++i)strcat(text,"nr_subsys_controller_extra 0\n");
  if(strcmp(argv[1],"missing_dying"))strcat(text,"nr_dying_descendants 0\n");
  if(!strcmp(argv[1],"duplicate"))strcat(text,"nr_descendants 0\n");
  if(!strcmp(argv[1],"oversize"))for(int i=0;i<300;++i)strcat(text,"nr_subsys_more 0\n");
  int f=openat(d,"cgroup.stat",O_WRONLY|O_CREAT|O_EXCL,0600);
  if(f<0 || write(f,text,strlen(text))!=(ssize_t)strlen(text))return 6;close(f);
  int allowed=no_descendants(d);
  bad=!strcmp(argv[1],"kernel_schema") ? !allowed : allowed;
 }else if(!strcmp(argv[1],"empty")) {
  int f=openat(d,"cgroup.events",O_WRONLY|O_CREAT|O_EXCL,0600);
  if(f<0 || write(f,"populated 1\n",12)!=12)return 6;close(f);
  bad=empty_D(d);
 }
 close(anchor);close(d);close(parent);return bad?7:0;
}
""")
    binary = tmp_path / "probe"
    built = subprocess.run(
        ["cc", "-std=c11", "-O0", "-I", str(native.parent), "-o", str(binary), str(probe)],
        capture_output=True,
    )
    assert built.returncode == 0, built.stderr
    result = subprocess.run([str(binary), case, str(tmp_path)], capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr
