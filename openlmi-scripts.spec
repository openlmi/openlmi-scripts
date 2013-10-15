%global         commands logicalfile service software storage

Name:           openlmi-scripts
Version:        0.2.3
Release:        1%{?dist}
Summary:        Client-side python modules and command line utilities

License:        BSD
URL:            http://fedorahosted.org/openlmi
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python2-devel
# For documentation
BuildRequires:  python-sphinx
BuildRequires:  python-sphinx-theme-openlmi
BuildRequires:  openlmi-tools
Requires:       python2
Requires:       openlmi-python-base >= 0.1.1
Requires:       python-docopt >= 0.6.1
Requires:       openlmi-tools

%description
Client-side python modules and command line utilities.

%package        doc
Summary:        OpenLMI scripts documentation
Group:          Documentation

%description    doc
This package contains the documents for OpenLMI Scripts.

%package        logicalfile
Summary:        Client scripts for OpenLMI Logical File provider
Version:        0.0.1
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    logicalfile
This packages contains client side python library for OpenLMI Logical File
provider and command line wrapper.

%package        service
Summary:        Client scripts for OpenLMI Service provider
Version:        0.1.0
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    service
This packages contains client side python library for OpenLMI Service
provider and command line wrapper.

%package        software
Summary:        Client scripts for OpenLMI Software provider
Version:        0.2.1
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    software
This packages contains client side python library for OpenLMI Software
provider and command line wrapper.

%package        storage
Summary:        Client scripts for OpenLMI Storage provider
Version:        0.0.2
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    storage
This packages contains client side python library for OpenLMI Storage
provider and command line wrapper.

%prep
%setup -q

%build
%{__python} setup.py build
for cmd in %{commands}; do
    pushd commands/$cmd
    %{__python} setup.py build
    popd
done
make -C man
INCLUDE_COMMANDS=1 COMMANDS="%{commands}" make -C doc html

%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
for cmd in %{commands}; do
    pushd commands/$cmd
    %{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
    popd
done
# copy init module for namespace package
# without it the imports from eggs installed to user directory would not work
cp -p lmi/scripts/__init__.* $RPM_BUILD_ROOT%{python_sitelib}/lmi/scripts

# install config file
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/openlmi/scripts
install -m 0644 config/lmi.conf $RPM_BUILD_ROOT%{_sysconfdir}/openlmi/scripts

# install man page
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1
install -m 0644 man/lmi.1.gz $RPM_BUILD_ROOT%{_mandir}/man1

# install bash completion
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/bash_completion.d
install -m 0644 completion/lmi.bash $RPM_BUILD_ROOT%{_sysconfdir}/bash_completion.d
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/lmi-bash-completion
install -m 0755 completion/lmi-bash-completion/print_possible_commands.sh \
     $RPM_BUILD_ROOT%{_libexecdir}/lmi-bash-completion
cp -pr completion/lmi-bash-completion/commands \
    $RPM_BUILD_ROOT%{_libexecdir}/lmi-bash-completion

# install documentation
install -m 755 -d $RPM_BUILD_ROOT%{_docdir}/%{name}/html
cp -pr doc/_build/html/* $RPM_BUILD_ROOT%{_docdir}/%{name}/html
install -m 644 README.md COPYING Changelog $RPM_BUILD_ROOT/%{_docdir}/%{name}

%files
%doc %{_docdir}/%{name}/README.md
%doc %{_docdir}/%{name}/COPYING
%doc %{_docdir}/%{name}/Changelog
%{_bindir}/lmi
%config(noreplace) %{_sysconfdir}/openlmi/scripts/lmi.conf
%config(noreplace) %{_sysconfdir}/bash_completion.d/lmi.bash
%dir %{_libexecdir}/lmi-bash-completion
%dir %{_libexecdir}/lmi-bash-completion/commands
%{_libexecdir}/lmi-bash-completion/*.sh
%{_libexecdir}/lmi-bash-completion/commands/_help
%dir %{python_sitelib}/lmi/scripts
%{_mandir}/man1/lmi.1.gz
%{python_sitelib}/lmi/scripts/__init__.py*
%{python_sitelib}/lmi/scripts/common
%{python_sitelib}/lmi/scripts/_metacommand
%{python_sitelib}/openlmi_scripts-*

%files doc
%{_docdir}/%{name}/html

%files logicalfile
%doc commands/logicalfile/README.md COPYING
%dir %{python_sitelib}/lmi/scripts/logicalfile
%{python_sitelib}/lmi/scripts/logicalfile/*
%{python_sitelib}/openlmi_scripts_logicalfile-*

%files service
%doc commands/service/README.md COPYING
%dir %{python_sitelib}/lmi/scripts/service
%{python_sitelib}/lmi/scripts/service/*
%{python_sitelib}/openlmi_scripts_service-*

%files software
%doc commands/software/README.md COPYING
%dir %{python_sitelib}/lmi/scripts/software
%{python_sitelib}/lmi/scripts/software/*
%{python_sitelib}/openlmi_scripts_software-*

%files storage
%doc commands/storage/README.md COPYING
%dir %{python_sitelib}/lmi/scripts/storage
%{python_sitelib}/lmi/scripts/storage/*
%{python_sitelib}/openlmi_scripts_storage-*

%changelog
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

