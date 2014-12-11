%global         commit e7ada516f51b2e0c19290a6bbb5c6dd9d9d50903
%global         shortcommit %(c=%{commit}; echo ${c:0:7})
%global         commands account hardware journald locale logicalfile networking
%global         commands %{commands} powermanagement realmd selinux service
%global         commands %{commands} software sssd storage
%global         commands %{commands} system
%global         tools_version 0.10.4

Name:           openlmi-scripts
Version:        0.4.0
Release:        1%{?dist}
Summary:        Client-side python modules and command line utilities

License:        BSD
URL:            http://fedorahosted.org/openlmi
Source0:        https://github.com/openlmi/%{name}/archive/%{commit}/%{name}-%{version}-%{shortcommit}.tar.gz
BuildArch:      noarch

BuildRequires:  python2-devel
# For documentation
BuildRequires:  python-docopt
BuildRequires:  python-sphinx
BuildRequires:  python-sphinx_rtd_theme
BuildRequires:  openlmi-tools >= %{tools_version}
BuildRequires:  python-IPy

Requires:       %{name}-account         = %{version}-%{release}
Requires:       %{name}-hardware        = %{version}-%{release}
Requires:       %{name}-journald        = %{version}-%{release}
Requires:       %{name}-locale          = %{version}-%{release}
Requires:       %{name}-logicalfile     = %{version}-%{release}
Requires:       %{name}-networking      = %{version}-%{release}
Requires:       %{name}-powermanagement = %{version}-%{release}
Requires:       %{name}-realmd          = %{version}-%{release}
Requires:       %{name}-selinux         = %{version}-%{release}
Requires:       %{name}-service         = %{version}-%{release}
Requires:       %{name}-software        = %{version}-%{release}
Requires:       %{name}-sssd            = %{version}-%{release}
Requires:       %{name}-storage         = %{version}-%{release}
Requires:       %{name}-system          = %{version}-%{release}

%description
Client-side python modules and command line utilities for OpenLMI providers.

%package        account
Summary:        Client scripts for OpenLMI Account provider
Requires:       openlmi-tools >= %{tools_version}

%description    account
This package contains client side python library for OpenLMI Account
provider and command line wrapper.

%package        hardware
Summary:        Client scripts for OpenLMI Hardware provider
Requires:       openlmi-tools >= %{tools_version}

%description    hardware
This package contains client side python library for OpenLMI Hardware
provider and command line wrapper.

%package        journald
Summary:        Client scripts for OpenLMI Journald provider
Requires:       openlmi-tools >= %{tools_version}

%description    journald
This package contains client side python library for OpenLMI Journald
provider and command line wrapper.

%package        locale
Summary:        Client scripts for OpenLMI Locale provider
Requires:       openlmi-tools >= %{tools_version}

%description    locale
This package contains client side python library for OpenLMI Locale
provider and command line wrapper.

%package        logicalfile
Summary:        Client scripts for OpenLMI Logical File provider
Requires:       openlmi-tools >= %{tools_version}

%description    logicalfile
This package contains client side python library for OpenLMI Logical File
provider and command line wrapper.

%package        networking
Summary:        Client scripts for OpenLMI Networking provider
Requires:       openlmi-tools >= %{tools_version}
Requires:       python-IPy

%description    networking
This package contains client side python library for OpenLMI Networking
provider and command line wrapper.

%package        powermanagement
Summary:        Client scripts for OpenLMI Power provider
Requires:       openlmi-tools >= %{tools_version}

%description    powermanagement
This package contains client side python library for OpenLMI PowerManagement
provider and command line wrapper.

%package        realmd
Summary:        Client scripts for OpenLMI Realmd provider
Requires:       openlmi-tools >= %{tools_version}

%description    realmd
This package contains client side python library for OpenLMI Realmd
provider and command line wrapper.

%package        selinux
Summary:        Client scripts for OpenLMI SELinux provider
Requires:       %{name} = %{version}-%{release}

%description    selinux
This package contains client side python library for OpenLMI SELinux provider
and command line wrapper.


%package        service
Summary:        Client scripts for OpenLMI Service provider
Requires:       openlmi-tools >= %{tools_version}

%description    service
This package contains client side python library for OpenLMI Service
provider and command line wrapper.

%package        software
Summary:        Client scripts for OpenLMI Software provider
Requires:       openlmi-tools >= %{tools_version}

%description    software
This package contains client side python library for OpenLMI Software
provider and command line wrapper.

%package        sssd
Summary:        Client scripts for OpenLMI SSSD provider
Requires:       openlmi-tools = %{version}-%{release}

%description    sssd
This package contains client side python library for OpenLMI SSSD provider and
command line wrapper.

%package        storage
Summary:        Client scripts for OpenLMI Storage provider
Requires:       openlmi-tools >= %{tools_version}

%description    storage
This package contains client side python library for OpenLMI Storage
provider and command line wrapper.

%package        system
Summary:        Client scripts providing general system information
Requires:       openlmi-tools >= %{tools_version}
Requires:       %{name}-service >= %{version}

%description    system
This package contains client side python library for few OpenLMI providers and
command line wrapper. It's aimed to provide some general information about
system.


%prep
%setup -qn %{name}-%{commit}

%build
# build scripts and their documentation
COMMANDS="%{commands}" make setup-all
for cmd in %{commands}; do
    pushd commands/$cmd
        %{__python2} setup.py build
        cd doc
        make html
        [ -e _build/html/.buildinfo ] && rm _build/html/.buildinfo
    popd # commands/$cmd
done

%install
# install scripts and their documentation
for cmd in %{commands}; do
    pushd commands/$cmd
        %{__python2} setup.py install -O1 --skip-build --root %{buildroot}
        install -m 0755 -d %{buildroot}%{_docdir}/%{name}-$cmd
        cp -rp doc/_build/html %{buildroot}%{_docdir}/%{name}-$cmd
        install -m 0644 README.md ../../COPYING \
                %{buildroot}%{_docdir}/%{name}-$cmd
    popd # commands/$cmd
done

# install documentation
install -m 0755 -d %{buildroot}%{_docdir}/%{name}
install -m 0644 README.md COPYING %{buildroot}%{_docdir}/%{name}

%files
%doc %{_docdir}/%{name}/README.md
%doc %{_docdir}/%{name}/COPYING

%files account
%doc %{_docdir}/%{name}-account/
%{python2_sitelib}/lmi/scripts/account/
%{python2_sitelib}/openlmi_scripts_account-*

%files hardware
%doc %{_docdir}/%{name}-hardware/
%{python2_sitelib}/lmi/scripts/hardware/
%{python2_sitelib}/openlmi_scripts_hardware-*

%files journald
%doc %{_docdir}/%{name}-journald/
%{python2_sitelib}/lmi/scripts/journald/
%{python2_sitelib}/openlmi_scripts_journald-*

%files locale
%doc %{_docdir}/%{name}-locale/
%{python2_sitelib}/lmi/scripts/locale/
%{python2_sitelib}/openlmi_scripts_locale-*

%files logicalfile
%doc %{_docdir}/%{name}-logicalfile/
%{python2_sitelib}/lmi/scripts/logicalfile/
%{python2_sitelib}/openlmi_scripts_logicalfile-*

%files networking
%doc %{_docdir}/%{name}-networking/
%{python2_sitelib}/lmi/scripts/networking/
%{python2_sitelib}/openlmi_scripts_networking-*

%files powermanagement
%doc %{_docdir}/%{name}-powermanagement/
%{python2_sitelib}/lmi/scripts/powermanagement/
%{python2_sitelib}/openlmi_scripts_powermanagement-*

%files realmd
%doc %{_docdir}/%{name}-realmd/
%{python2_sitelib}/lmi/scripts/realmd/
%{python2_sitelib}/openlmi_scripts_realmd-*

%files selinux
%doc %{_docdir}/%{name}-selinux/
%{python2_sitelib}/lmi/scripts/selinux/
%{python2_sitelib}/openlmi_scripts_selinux-*

%files service
%doc %{_docdir}/%{name}-service/
%{python2_sitelib}/lmi/scripts/service/
%{python2_sitelib}/openlmi_scripts_service-*

%files software
%doc %{_docdir}/%{name}-software/
%{python2_sitelib}/lmi/scripts/software/
%{python2_sitelib}/openlmi_scripts_software-*

%files sssd
%doc %{_docdir}/%{name}-sssd/
%{python2_sitelib}/lmi/scripts/sssd/
%{python2_sitelib}/openlmi_scripts_sssd-*

%files storage
%doc %{_docdir}/%{name}-storage/
%{python2_sitelib}/lmi/scripts/storage/
%{python2_sitelib}/openlmi_scripts_storage-*

%files system
%doc %{_docdir}/%{name}-system/
%{python2_sitelib}/lmi/scripts/system/
%{python2_sitelib}/openlmi_scripts_system-*

%changelog
* Thu Dec 11 2014 Michal Minar <miminar@redhat.com> 0.4.0-1
- New upstream release.
- New subpackages: locale, realmd, sssd, selinux.

* Tue Apr 29 2014 Michal Minar <miminar@redhat.com> 0.3.0-1
- Requirement fixes.
- Small bugfixes and logging improvements.

* Thu Apr 24 2014 Michal Minar <miminar@redhat.com> 0.2.8-1
- Meta-command is not shipped any more (moved to openlmi-tools).
- Base package now just groups script subpackages.
- Particular subpackages now depend just on openlmi-tools.
- Added journald scripts.

* Mon Mar 10 2014 Michal Minar <miminar@redhat.com> 0.2.7-8
- Fixed listing of thin volumes/groups in provides.
- Smart hostname selection when no hosts are given.
- System command improvements.
- Fixed storage error reporting.

* Wed Mar 05 2014 Michal Minar <miminar@redhat.com> 0.2.7-7
- Fixed few networking bugs.
- Fixed duplicate headers.

* Tue Mar 04 2014 Michal Minar <miminar@redhat.com> 0.2.7-6
- Fixed search command of software scripts.

* Wed Feb 26 2014 Michal Minar <miminar@redhat.com> 0.2.7-5
- Fixed error handling in service scripts.
- Updated documentation for built-ins commands.
- Fixed checking for thinlv provisioning in storage scripts.

* Tue Feb 25 2014 Michal Minar <miminar@redhat.com> 0.2.7-4
- Removed unstable features from hardware scripts.

* Tue Feb 25 2014 Michal Minar <miminar@redhat.com> 0.2.7-3
- Added account and powermanagement commands.

* Tue Feb 25 2014 Michal Minar <miminar@redhat.com> 0.2.7-2
- Fixed storage mount list command.

* Tue Feb 25 2014 Michal Minar <miminar@redhat.com> 0.2.7-1
- Support older OpenLMI Hardware providers.
- Resolves: bz#1069320

* Mon Feb 24 2014 Michal Minar <miminar@redhat.com> 0.2.7-0
- New upstream version.
- Added system library.

* Wed Jan 15 2014 Michal Minar <miminar@redhat.com> 0.2.6-5
- Added networking library.

* Mon Jan 13 2014 Michal Minar <miminar@redhat.com> 0.2.5-4
- New upstream version.

* Mon Nov 11 2013 Michal Minar <miminar@redhat.com> 0.2.4a-3
- Fixed dependency on openlmi-scripts for subpackages.

* Wed Nov 06 2013 Michal Minar <miminar@redhat.com> 0.2.4a-2
- New upstream version.
- Require openlmi-tools 0.9.

* Tue Oct 29 2013 Michal Minar <miminar@redhat.com> 0.2.3-5
- Made the build dependency on openlmi-tools version specific.

* Tue Oct 29 2013 Michal Minar <miminar@redhat.com> 0.2.3-4
- Fixed build, installation problems and rpmlint errors.

* Thu Oct 17 2013 Michal Minar <miminar@redhat.com> 0.2.3-3
- Require python-docopt on build.
- Do not make configs out of completion scripts.
- Removed _isa macros.

* Wed Oct 16 2013 Michal Minar <miminar@redhat.com> 0.2.3-2
- Require openlmi-providers.
- Own config directory.

* Mon Oct 14 2013 Michal Minar <miminar@redhat.com> 0.2.3-1
- Rebased to 0.2.3
- Added bash completion.
- Added documentation.
- Extended installed commands.
- Divided into subpackages.

* Fri Aug 09 2013 Michal Minar <miminar@redhat.com> 0.1.1-1
- Rebased to 0.1.1

* Thu Aug 08 2013 Michal Minar <miminar@redhat.com> 0.1.0-1
- Initial version.

