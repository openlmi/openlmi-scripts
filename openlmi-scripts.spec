%global         commands service

Name:		openlmi-scripts
Version:	0.1.1
Release:	1%{?dist}
Summary:	Client-side python modules and command line utilities

License:	BSD
URL:		http://fedorahosted.org/openlmi
Source0:	%{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:	python2-devel
Requires:	python2
Requires:       openlmi-python-base >= 0.1.1
Requires:       python-docopt >= 0.6.1

%description
Client-side python modules and command line utilities.

%prep
%setup -q

%build
%{__python} setup.py build
for cmd in %{commands}; do
    pushd commands/$cmd
    %{__python} setup.py build
    popd
done

%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
for cmd in %{commands}; do
    pushd commands/$cmd
    %{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
    popd
done
mkdir -p $RPM_BUILD_ROOT/etc/openlmi/scripts
install -m 0644 config/lmi.conf $RPM_BUILD_ROOT/etc/openlmi/scripts

%files
%doc README.md COPYING Changelog
%{_bindir}/lmi
%{_sysconfig}/openlmi/scripts/lmi.conf
%dir %{python_sitelib}/lmi/scripts
%{python_sitelib}/lmi/scripts/*
%{python_sitelib}/lmi_scripts-*
%{python_sitelib}/lmi_scripts_service-*

%changelog
* Fri Aug 09 2013 Michal Minar <miminar@redhat.com> 0.1.1-1
- Rebased to 0.1.1

* Thu Aug 08 2013 Michal Minar <miminar@redhat.com> 0.1.0-1
- Initial version.

