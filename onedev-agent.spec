%undefine _debugsource_packages

%global __java_requires %{nil}
%global __java_provides %{nil}
%global __jmod_requires %{nil}
%global __jmod_provides %{nil}
%global __osgi_requires %{nil}
%global __osgi_provides %{nil}

%global rootpath /srv/%{name}
%global confpath %{rootpath}/conf
%global libpath %{rootpath}/lib
%global logpath %{rootpath}/logs
%global workpath %{rootpath}/work

Name:      onedev-agent
Version:   2.4.1
Release:   2
Summary:   Build agent/executor for OneDev
URL:       https://code.onedev.io/onedev/agent
License:   MIT
Group:     Servers

# List of available releases:
# https://code.onedev.io/onedev/agent/~builds?query=%22Job%22+is+%22Release%22+and+successful
# https://code.onedev.io/~downloads/projects/235/archives?revision=refs/tags/v%{version}&format=tgz
Source0:   %{name}-%{version}.tar.gz
Source1:   %{name}-%{version}-deps.tar.zst
Source10:  %{name}.sysusers
Source20:  agent.properties
Source30:  tanuki-wrapper.conf

Patch0:  disable-autoupdate.patch

BuildRequires:  jdk-current
BuildRequires:  maven >= 3.8.1
BuildRequires:  tanuki-wrapper

Requires:  docker
Requires:  git
Requires:  git-lfs
Requires:  tanuki-wrapper

%description
Build agent/executor for OneDev

%prep
%autosetup -a 1 -p 1 -c

%build
%{_datadir}/maven/bin/mvn -Dmaven.repo.local=repository \
    -DskipTests \
    package

%install
mkdir -p %{buildroot}%{confpath} \
         %{buildroot}%{libpath} \
         %{buildroot}%{logpath} \
         %{buildroot}%{workpath}

# Main JAR
mv target/agent-%{version}.jar \
    %{buildroot}%{rootpath}/%{name}.jar

# Dependencies
%{_datadir}/maven/bin/mvn dependency:copy-dependencies \
    -Dmaven.repo.local=repository \
    -DincludeScope=runtime \
    -DoutputDirectory=%{buildroot}%{libpath}

# Systemd integration
. /etc/profile.d/90java.sh

mkdir -p %{buildroot}%{_unitdir}
cat >%{buildroot}%{_unitdir}/%{name}.service <<EOF
[Unit]
Description=Build agent/executor for OneDev
After=syslog.target network-online.target

[Service]
Type=simple
User=%{name}
Group=%{name}
ExecStart=tanuki-wrapper %{confpath}/tanuki-wrapper.conf \
wrapper.pidfile="%{_rundir}/%{name}/tanuki-wrapper.pid"
RuntimeDirectory=%{name}
RuntimeDirectoryMode=0700
Environment=JAVA_HOME=$JAVA_HOME

[Install]
WantedBy=multi-user.target
EOF

# User
mkdir -p %{buildroot}%{_sysusersdir}
cp %{S:10} %{buildroot}%{_sysusersdir}/%{name}.conf

# Config
cp %{S:20} %{buildroot}%{confpath}/
cp %{S:30} %{buildroot}%{confpath}/
cp src/main/resources/agent/conf/logback.xml %{buildroot}%{confpath}/

touch %{buildroot}%{confpath}/attributes.properties

# A random UUID is written into this test file to check permissions
touch %{buildroot}%{rootpath}/test

%post
# Allow r/w access to namespaced Docker containers
setfacl -m g:100000:rwx %{workpath}
setfacl -m d:g:100000:rwx %{workpath}

%files
%doc README.md
%license license.txt
%{_sysusersdir}/%{name}.conf
%{_unitdir}/%{name}.service

%dir %attr(0755,root,root) %{rootpath}
%dir %attr(0770,root,%{name}) %{confpath}
%dir %attr(0755,root,root) %{libpath}
%dir %attr(0770,root,%{name}) %{logpath}
%dir %attr(0770,root,%{name}) %{workpath}

%config(noreplace) %attr(0660,root,%{name}) %{confpath}/attributes.properties
%config(noreplace) %attr(0640,root,%{name}) %{confpath}/agent.properties
%attr(0640,root,%{name}) %{confpath}/logback.xml
%attr(0640,root,%{name}) %{confpath}/tanuki-wrapper.conf
%attr(0644,root,root) %{rootpath}/%{name}.jar
%attr(0644,root,root) %{libpath}/*

%attr(0664,root,%{name}) %{rootpath}/test
