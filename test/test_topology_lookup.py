"""
Unit Tests for TopologyLookup Utility

This module contains comprehensive unit tests for the topology_lookup module.
"""

import unittest
from src.topology_lookup import TopologyLookup, Resource


class TestResource(unittest.TestCase):
    """Tests for the Resource dataclass."""
    
    def test_resource_creation(self):
        """Test creating a basic resource."""
        resource = Resource(
            resId="test-id-123",
            name="TestResource",
            resource_type="FixedNetworkElement"
        )
        
        self.assertEqual(resource.resId, "test-id-123")
        self.assertEqual(resource.name, "TestResource")
        self.assertEqual(resource.resource_type, "FixedNetworkElement")
        self.assertEqual(resource.properties, {})
    
    def test_resource_with_properties(self):
        """Test creating a resource with properties."""
        props = {"key1": "value1", "key2": 123}
        resource = Resource(
            resId="test-id-456",
            name="TestResource2",
            resource_type="FixedNetworkCard",
            properties=props
        )
        
        self.assertEqual(resource.properties, props)


class TestTopologyLookupInit(unittest.TestCase):
    """Tests for TopologyLookup initialization."""
    
    def test_initialization(self):
        """Test that TopologyLookup initializes correctly."""
        lookup = TopologyLookup()
        
        # Check all supported types are initialized
        for resource_type in TopologyLookup.SUPPORTED_RESOURCE_TYPES:
            self.assertIn(resource_type, lookup._resources)
            self.assertEqual(len(lookup._resources[resource_type]), 0)
        
        # Check name index is empty
        self.assertEqual(len(lookup._name_index), 0)
    
    def test_supported_types(self):
        """Test getting supported resource types."""
        lookup = TopologyLookup()
        types = lookup.get_supported_types()
        
        self.assertEqual(len(types), len(TopologyLookup.SUPPORTED_RESOURCE_TYPES))
        self.assertEqual(types, TopologyLookup.SUPPORTED_RESOURCE_TYPES)


class TestAddResource(unittest.TestCase):
    """Tests for adding resources."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
    
    def test_add_fixed_network_element(self):
        """Test adding a FixedNetworkElement resource."""
        resource = self.lookup.add_resource(
            resource_type="FixedNetworkElement",
            resId="ne-id-001",
            name="NE-CityB-DIST-44"
        )
        
        self.assertEqual(resource.resId, "ne-id-001")
        self.assertEqual(resource.name, "NE-CityB-DIST-44")
        self.assertEqual(resource.resource_type, "FixedNetworkElement")
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkElement"), 1)
    
    def test_add_resource_with_properties(self):
        """Test adding a resource with properties."""
        props = {"FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"}
        resource = self.lookup.add_resource(
            resource_type="FixedNetworkCard",
            resId="card-id-001",
            name="TPA2EG24 24",
            properties=props
        )
        
        self.assertEqual(resource.properties["FixedNetworkElement.refParentNE"], 
                        "BR-CityB-ACC-54")
    
    def test_add_unsupported_resource_type(self):
        """Test that adding unsupported resource type raises ValueError."""
        with self.assertRaises(ValueError):
            self.lookup.add_resource(
                resource_type="InvalidType",
                resId="invalid-id",
                name="Invalid"
            )
    
    def test_add_multiple_resources_same_type(self):
        """Test adding multiple resources of the same type."""
        self.lookup.add_resource("FixedNetworkElement", "id1", "NE1")
        self.lookup.add_resource("FixedNetworkElement", "id2", "NE2")
        self.lookup.add_resource("FixedNetworkElement", "id3", "NE3")
        
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkElement"), 3)
    
    def test_add_resources_different_types(self):
        """Test adding resources of different types."""
        self.lookup.add_resource("FixedNetworkElement", "ne1", "NE1")
        self.lookup.add_resource("FixedNetworkCard", "card1", "Card1")
        self.lookup.add_resource("FixedNetworkLTP", "ltp1", "LTP1")
        
        self.assertEqual(self.lookup.get_resource_count(), 3)
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkElement"), 1)
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkCard"), 1)
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkLTP"), 1)


class TestLoadFromDict(unittest.TestCase):
    """Tests for loading resources from dictionary."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
    
    def test_load_from_dict(self):
        """Test loading resources from dictionary structure."""
        data = {
            "FixedNetworkElement": [
                {"resId": "ne1", "name": "NE1"},
                {"resId": "ne2", "name": "NE2"}
            ],
            "FixedNetworkCard": [
                {"resId": "card1", "name": "Card1", "prop1": "value1"}
            ]
        }
        
        count = self.lookup.load_from_dict(data)
        
        self.assertEqual(count, 3)
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkElement"), 2)
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkCard"), 1)
    
    def test_load_from_dict_ignores_unsupported_types(self):
        """Test that unsupported types are ignored."""
        data = {
            "FixedNetworkElement": [{"resId": "ne1", "name": "NE1"}],
            "UnsupportedType": [{"resId": "bad1", "name": "Bad"}]
        }
        
        count = self.lookup.load_from_dict(data)
        
        self.assertEqual(count, 1)
        self.assertIsNone(self.lookup.find_resource_by_id("bad1"))
    
    def test_load_from_dict_empty(self):
        """Test loading empty dictionary."""
        count = self.lookup.load_from_dict({})
        self.assertEqual(count, 0)


class TestFindResourceById(unittest.TestCase):
    """Tests for finding resources by ID."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
        self.lookup.add_resource("FixedNetworkElement", "ne1", "NE1")
        self.lookup.add_resource("FixedNetworkCard", "card1", "Card1")
    
    def test_find_existing_resource(self):
        """Test finding an existing resource by ID."""
        resource = self.lookup.find_resource_by_id("ne1")
        
        self.assertIsNotNone(resource)
        self.assertEqual(resource.name, "NE1")
        self.assertEqual(resource.resource_type, "FixedNetworkElement")
    
    def test_find_nonexistent_resource(self):
        """Test finding a non-existent resource."""
        resource = self.lookup.find_resource_by_id("nonexistent")
        self.assertIsNone(resource)
    
    def test_find_resource_by_id_and_type(self):
        """Test finding resource by ID and type."""
        resource = self.lookup.find_resource_by_id_and_type("ne1", "FixedNetworkElement")
        self.assertIsNotNone(resource)
        self.assertEqual(resource.name, "NE1")
    
    def test_find_resource_wrong_type(self):
        """Test finding resource with wrong type returns None."""
        resource = self.lookup.find_resource_by_id_and_type("ne1", "FixedNetworkCard")
        self.assertIsNone(resource)


class TestFindResourcesByType(unittest.TestCase):
    """Tests for finding resources by type."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
        self.lookup.add_resource("FixedNetworkElement", "ne1", "NE1")
        self.lookup.add_resource("FixedNetworkElement", "ne2", "NE2")
        self.lookup.add_resource("FixedNetworkCard", "card1", "Card1")
    
    def test_find_all_resources_of_type(self):
        """Test finding all resources of a specific type."""
        resources = self.lookup.find_resources_by_type("FixedNetworkElement")
        
        self.assertEqual(len(resources), 2)
        names = {r.name for r in resources}
        self.assertEqual(names, {"NE1", "NE2"})
    
    def test_find_resources_unsupported_type(self):
        """Test finding resources of unsupported type returns empty list."""
        resources = self.lookup.find_resources_by_type("InvalidType")
        self.assertEqual(resources, [])
    
    def test_find_resources_empty_type(self):
        """Test finding resources of type with no resources."""
        resources = self.lookup.find_resources_by_type("FixedNetworkLTP")
        self.assertEqual(resources, [])


class TestFindResourcesByName(unittest.TestCase):
    """Tests for finding resources by name."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
        self.lookup.add_resource("FixedNetworkElement", "ne1", "NE-CityB-DIST-44")
        self.lookup.add_resource("FixedNetworkElement", "ne2", "BR-CityB-ACC-54")
        self.lookup.add_resource("FixedNetworkCard", "card1", "TPA2EG24 24")
    
    def test_find_by_exact_name(self):
        """Test finding resource by exact name match."""
        resources = self.lookup.find_resources_by_name("NE-CityB-DIST-44", exact_match=True)
        
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].name, "NE-CityB-DIST-44")
    
    def test_find_by_partial_name(self):
        """Test finding resource by partial name match."""
        resources = self.lookup.find_resources_by_name("CityB")
        
        self.assertEqual(len(resources), 2)
        names = {r.name for r in resources}
        self.assertIn("NE-CityB-DIST-44", names)
        self.assertIn("BR-CityB-ACC-54", names)
    
    def test_find_by_name_no_match(self):
        """Test finding resource with no matches."""
        resources = self.lookup.find_resources_by_name("NonExistent")
        self.assertEqual(resources, [])
    
    def test_find_duplicate_names(self):
        """Test finding resources with duplicate names."""
        self.lookup.add_resource("FixedNetworkCard", "card2", "TPA2EG24 24")
        
        resources = self.lookup.find_resources_by_name("TPA2EG24 24", exact_match=True)
        self.assertEqual(len(resources), 2)


class TestFindParentResource(unittest.TestCase):
    """Tests for finding parent resources."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
        
        # Set up a parent-child relationship
        self.lookup.add_resource(
            "FixedNetworkElement", 
            "ne1", 
            "BR-CityB-ACC-54"
        )
        self.lookup.add_resource(
            "FixedNetworkCard",
            "card1",
            "TPA2EG24 24",
            {"FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"}
        )
    
    def test_find_parent_resource(self):
        """Test finding parent resource from child."""
        child = self.lookup.find_resource_by_id("card1")
        parent = self.lookup.find_parent_resource(
            child, 
            "FixedNetworkElement.refParentNE"
        )
        
        self.assertIsNotNone(parent)
        self.assertEqual(parent.name, "BR-CityB-ACC-54")
        self.assertEqual(parent.resource_type, "FixedNetworkElement")
    
    def test_find_parent_nonexistent_reference(self):
        """Test finding parent when reference doesn't exist."""
        child = self.lookup.find_resource_by_id("card1")
        parent = self.lookup.find_parent_resource(
            child, 
            "NonExistentField"
        )
        self.assertIsNone(parent)
    
    def test_find_parent_missing_value(self):
        """Test finding parent when reference value is missing."""
        self.lookup.add_resource(
            "FixedNetworkCard",
            "card2",
            "TPA1EX8S 21"
            # No FixedNetworkElement.refParentNE property
        )
        child = self.lookup.find_resource_by_id("card2")
        parent = self.lookup.find_parent_resource(
            child,
            "FixedNetworkElement.refParentNE"
        )
        self.assertIsNone(parent)


class TestFindChildResources(unittest.TestCase):
    """Tests for finding child resources."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
        
        # Set up parent
        self.lookup.add_resource(
            "FixedNetworkElement",
            "ne1",
            "BR-CityB-ACC-54"
        )
        
        # Set up multiple children referencing the parent
        self.lookup.add_resource(
            "FixedNetworkCard",
            "card1",
            "TPA2EG24 24",
            {"FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"}
        )
        self.lookup.add_resource(
            "FixedNetworkCard",
            "card2",
            "TPB1FAN 30",
            {"FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"}
        )
        self.lookup.add_resource(
            "FixedNetworkCard",
            "card3",
            "Other Card",
            {"FixedNetworkElement.refParentNE": "Other NE"}
        )
    
    def test_find_all_children(self):
        """Test finding all child resources."""
        parent = self.lookup.find_resource_by_id("ne1")
        children = self.lookup.find_child_resources(parent)
        
        self.assertEqual(len(children), 2)
        child_names = {c['child'].name for c in children}
        self.assertIn("TPA2EG24 24", child_names)
        self.assertIn("TPB1FAN 30", child_names)
    
    def test_find_children_specific_field(self):
        """Test finding children with specific reference field."""
        parent = self.lookup.find_resource_by_id("ne1")
        children = self.lookup.find_child_resources(
            parent,
            "FixedNetworkElement.refParentNE"
        )
        
        self.assertEqual(len(children), 2)
    
    def test_find_children_no_matches(self):
        """Test finding children when there are no matches."""
        self.lookup.add_resource(
            "FixedNetworkElement",
            "ne2",
            "Unreferenced NE"
        )
        parent = self.lookup.find_resource_by_id("ne2")
        children = self.lookup.find_child_resources(parent)
        self.assertEqual(children, [])


class TestGetResourceRelationships(unittest.TestCase):
    """Tests for getting resource relationships."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
        
        # Create a chain: Element -> Card -> LTP
        self.lookup.add_resource(
            "FixedNetworkElement",
            "ne1",
            "BR-CityB-ACC-54"
        )
        self.lookup.add_resource(
            "FixedNetworkCard",
            "card1",
            "TPA2EG24 24",
            {"FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"}
        )
        self.lookup.add_resource(
            "FixedNetworkLTP",
            "ltp1",
            "Trail-6977",
            {
                "FixedNetworkCard.refParentCard": "TPA2EG24 24",
                "FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"
            }
        )
    
    def test_get_relationships_for_card(self):
        """Test getting relationships for a card resource."""
        card = self.lookup.find_resource_by_id("card1")
        relationships = self.lookup.get_resource_relationships(card)
        
        # Should have one parent (the NE)
        self.assertEqual(len(relationships['parents']), 1)
        self.assertEqual(relationships['parents'][0]['parent'].name, "BR-CityB-ACC-54")
        
        # Should have one child (the LTP)
        self.assertEqual(len(relationships['children']), 1)
        self.assertEqual(relationships['children'][0]['child'].name, "Trail-6977")
    
    def test_get_relationships_for_element(self):
        """Test getting relationships for an element resource."""
        element = self.lookup.find_resource_by_id("ne1")
        relationships = self.lookup.get_resource_relationships(element)
        
        # Should have no parents (top-level)
        self.assertEqual(len(relationships['parents']), 0)
        
        # Should have two children (card and LTP both reference it)
        self.assertEqual(len(relationships['children']), 2)


class TestGetReferenceFields(unittest.TestCase):
    """Tests for getting reference fields."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
    
    def test_get_reference_fields_for_card(self):
        """Test getting reference fields for FixedNetworkCard."""
        fields = self.lookup.get_reference_fields("FixedNetworkCard")
        
        self.assertIn("FixedNetworkElement.refParentNE", fields)
        self.assertEqual(fields["FixedNetworkElement.refParentNE"], "FixedNetworkElement")
    
    def test_get_reference_fields_for_ltp(self):
        """Test getting reference fields for FixedNetworkLTP."""
        fields = self.lookup.get_reference_fields("FixedNetworkLTP")
        
        self.assertIn("FixedNetworkCard.refParentCard", fields)
        self.assertIn("FixedNetworkElement.refParentNE", fields)
        self.assertIn("FixedNetworkLTP.refParentLTP", fields)
        self.assertIn("FixedNetworkLTP.refTrunkLTP", fields)
    
    def test_get_reference_fields_unsupported_type(self):
        """Test getting reference fields for unsupported type."""
        fields = self.lookup.get_reference_fields("InvalidType")
        self.assertEqual(fields, {})


class TestClear(unittest.TestCase):
    """Tests for clearing resources."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
        self.lookup.add_resource("FixedNetworkElement", "ne1", "NE1")
        self.lookup.add_resource("FixedNetworkCard", "card1", "Card1")
    
    def test_clear_all_resources(self):
        """Test clearing all resources."""
        self.lookup.clear()
        
        self.assertEqual(self.lookup.get_resource_count(), 0)
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkElement"), 0)
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkCard"), 0)
    
    def test_clear_and_reuse(self):
        """Test that lookup can be reused after clearing."""
        self.lookup.clear()
        self.lookup.add_resource("FixedNetworkElement", "ne2", "NE2")
        
        self.assertEqual(self.lookup.get_resource_count(), 1)
        resource = self.lookup.find_resource_by_id("ne2")
        self.assertIsNotNone(resource)
        self.assertEqual(resource.name, "NE2")


class TestGetResourceCount(unittest.TestCase):
    """Tests for getting resource counts."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
    
    def test_count_empty(self):
        """Test count when empty."""
        self.assertEqual(self.lookup.get_resource_count(), 0)
    
    def test_count_specific_type(self):
        """Test counting specific type."""
        self.lookup.add_resource("FixedNetworkElement", "ne1", "NE1")
        self.lookup.add_resource("FixedNetworkElement", "ne2", "NE2")
        self.lookup.add_resource("FixedNetworkCard", "card1", "Card1")
        
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkElement"), 2)
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkCard"), 1)
    
    def test_count_total(self):
        """Test total count."""
        self.lookup.add_resource("FixedNetworkElement", "ne1", "NE1")
        self.lookup.add_resource("FixedNetworkCard", "card1", "Card1")
        self.lookup.add_resource("FixedNetworkLTP", "ltp1", "LTP1")
        
        self.assertEqual(self.lookup.get_resource_count(), 3)
    
    def test_count_unsupported_type(self):
        """Test counting unsupported type."""
        count = self.lookup.get_resource_count("InvalidType")
        self.assertEqual(count, 0)


class TestIntegrationWithRealData(unittest.TestCase):
    """Integration tests using data similar to topology_anonymized.md."""
    
    def setUp(self):
        self.lookup = TopologyLookup()
        
        # Load sample data from topology_anonymized.md
        data = {
            "FixedNetworkElement": [
                {"resId": "ad86ee9a-235e-11ea-b3e4-286ed4a6f27b", "name": "BR-CityB-ACC-54"},
                {"resId": "ad873c30-235e-11ea-b3e4-286ed4a6f27b", "name": "NE-CityB-DIST-44"},
                {"resId": "e0137928-af11-11ec-b48c-286ed4a6f23c", "name": "SW-CityA-DIST-69"}
            ],
            "FixedNetworkCard": [
                {
                    "resId": "68ae10be-235d-11ea-b4b3-286ed4a6f283",
                    "name": "TPA2EG24 24",
                    "FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"
                },
                {
                    "resId": "77838532-235d-11ea-a3da-286ed4a6f283",
                    "name": "CR57L5XFB 5/0",
                    "FixedNetworkElement.refParentNE": "NE-CityB-DIST-44"
                }
            ],
            "FixedNetworkLTP": [
                {
                    "resId": "779649db-235d-11ea-a3da-286ed4a6f283",
                    "name": "Eth-Trunk66",
                    "FixedNetworkElement.refParentNE": "NE-CityB-DIST-44"
                },
                {
                    "resId": "79a553f1-235d-11ea-b4b3-286ed4a6f283",
                    "name": "Trail-6977",
                    "FixedNetworkCard.refParentCard": "TPA2EG24 24",
                    "FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"
                }
            ]
        }
        
        self.lookup.load_from_dict(data)
    
    def test_load_and_query_real_data(self):
        """Test loading and querying real-world-like data."""
        # Verify counts
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkElement"), 3)
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkCard"), 2)
        self.assertEqual(self.lookup.get_resource_count("FixedNetworkLTP"), 2)
        
        # Find specific resource
        element = self.lookup.find_resource_by_id("ad86ee9a-235e-11ea-b3e4-286ed4a6f27b")
        self.assertIsNotNone(element)
        self.assertEqual(element.name, "BR-CityB-ACC-54")
    
    def test_traverse_relationships(self):
        """Test traversing relationships in real data."""
        # Find the Trail-6977 LTP
        ltp_list = self.lookup.find_resources_by_name("Trail-6977", exact_match=True)
        self.assertTrue(len(ltp_list) > 0)
        ltp = ltp_list[0]
        
        # Get its parent card
        parent_card = self.lookup.find_parent_resource(
            ltp,
            "FixedNetworkCard.refParentCard"
        )
        
        self.assertIsNotNone(parent_card)
        self.assertEqual(parent_card.name, "TPA2EG24 24")
        
        # Get the card's parent element
        parent_element = self.lookup.find_parent_resource(
            parent_card,
            "FixedNetworkElement.refParentNE"
        )
        
        self.assertIsNotNone(parent_element)
        self.assertEqual(parent_element.name, "BR-CityB-ACC-54")
    
    def test_find_children_of_element(self):
        """Test finding all children of a network element."""
        element_list = self.lookup.find_resources_by_name("BR-CityB-ACC-54", exact_match=True)
        self.assertTrue(len(element_list) > 0)
        element = element_list[0]
        children = self.lookup.find_child_resources(element)
        
        # Should find the card and the LTP that reference this element
        self.assertGreaterEqual(len(children), 2)
        
        child_names = {c['child'].name for c in children}
        self.assertIn("TPA2EG24 24", child_names)
        self.assertIn("Trail-6977", child_names)


if __name__ == '__main__':
    unittest.main()
