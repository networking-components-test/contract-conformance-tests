import unittest


PACKAGE_FAMILY = {
    "ncc-interfaces": {"role": "contracts", "depends_on": set()},
    "ncc-lib": {"role": "shared-library", "depends_on": {"ncc-interfaces"}},
    "ncc-clients": {
        "role": "generated-clients",
        "depends_on": {"ncc-interfaces", "ncc-lib"},
    },
    "ncc-cli": {
        "role": "operator-cli",
        "depends_on": {"ncc-interfaces", "ncc-lib", "ncc-clients"},
    },
}

DEPLOYABLE_SERVICES = {
    "ncc-dns-server",
    "ncc-vpn",
    "ncc-load-balancer",
    "ncc-switch",
    "ncc-router",
    "ncc-dhcp-server",
    "ncc-ipam",
    "ncc-firewall",
    "ncc-forward-proxy",
    "ncc-ntp",
    "ncc-stun-turn",
    "ncc-service-discovery",
    "ncc-network-controller",
    "ncc-observability",
    "ncc-pki",
}

# Audited from the connected production installation during DEN-2903 maintenance.
# This is deliberately fail-closed: publication is not inferred from a plan, issue,
# or package coordinate. Replace each value with an immutable repository/head proof
# only after the corresponding production repository actually exists.
PUBLICATION_EVIDENCE = {
    "ncc-interfaces": None,
    "ncc-lib": None,
    "ncc-clients": None,
    "ncc-cli": None,
}


class NccPackageFamilyTests(unittest.TestCase):
    def test_exact_short_name_family_and_roles(self) -> None:
        self.assertEqual(
            set(PACKAGE_FAMILY),
            {"ncc-interfaces", "ncc-lib", "ncc-clients", "ncc-cli"},
        )
        roles = {entry["role"] for entry in PACKAGE_FAMILY.values()}
        self.assertEqual(
            roles, {"contracts", "shared-library", "generated-clients", "operator-cli"}
        )

    def test_shared_packages_never_alias_deployable_services(self) -> None:
        self.assertTrue(set(PACKAGE_FAMILY).isdisjoint(DEPLOYABLE_SERVICES))

    def test_dependency_graph_is_downward_only_and_acyclic(self) -> None:
        expected = {
            "ncc-interfaces": set(),
            "ncc-lib": {"ncc-interfaces"},
            "ncc-clients": {"ncc-interfaces", "ncc-lib"},
            "ncc-cli": {"ncc-interfaces", "ncc-lib", "ncc-clients"},
        }
        self.assertEqual(
            {name: entry["depends_on"] for name, entry in PACKAGE_FAMILY.items()}, expected
        )

        visited: set[str] = set()
        active: set[str] = set()

        def visit(name: str) -> None:
            if name in active:
                self.fail(f"dependency cycle detected at {name}")
            if name in visited:
                return
            active.add(name)
            for dependency in PACKAGE_FAMILY[name]["depends_on"]:
                self.assertIn(dependency, PACKAGE_FAMILY)
                visit(dependency)
            active.remove(name)
            visited.add(name)

        for package in PACKAGE_FAMILY:
            visit(package)

    def test_publication_remains_fail_closed_without_repository_evidence(self) -> None:
        self.assertEqual(set(PUBLICATION_EVIDENCE), set(PACKAGE_FAMILY))
        self.assertTrue(
            all(value is None for value in PUBLICATION_EVIDENCE.values()),
            "do not claim package publication without immutable repository/head evidence",
        )


if __name__ == "__main__":
    unittest.main()
