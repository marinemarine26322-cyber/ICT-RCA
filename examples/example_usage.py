"""
Example usage of the ICT-RCA TopologyLookup utility.

This script demonstrates how to use the TopologyLookup class to work with
network topology data.

Run this script from the project root directory:
    python examples/example_usage.py
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.topology_lookup import TopologyLookup, Resource


def example_basic_usage():
    """Demonstrate basic usage of TopologyLookup."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    lookup = TopologyLookup()
    
    # Add resources
    lookup.add_resource(
        "FixedNetworkElement", 
        "ne1", 
        "BR-CityB-ACC-54"
    )
    lookup.add_resource(
        "FixedNetworkCard", 
        "card1", 
        "TPA2EG24 24",
        {"FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"}
    )
    lookup.add_resource(
        "FixedNetworkLTP", 
        "ltp1", 
        "Trail-6977",
        {
            "FixedNetworkCard.refParentCard": "TPA2EG24 24",
            "FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"
        }
    )
    
    # Find by ID
    resource = lookup.find_resource_by_id("ne1")
    print(f"\nFound resource by ID: {resource.name} ({resource.resource_type})")
    
    # Find by name
    resources = lookup.find_resources_by_name("CityB")
    print(f"Found {len(resources)} resources containing 'CityB'")
    
    # Get parent relationship
    card = lookup.find_resource_by_id("card1")
    parent = lookup.find_parent_resource(
        card, 
        "FixedNetworkElement.refParentNE"
    )
    print(f"Card '{card.name}' parent: {parent.name}")
    
    # Get child relationships
    element = lookup.find_resource_by_id("ne1")
    children = lookup.find_child_resources(element)
    print(f"Element '{element.name}' has {len(children)} children")
    
    # Get all relationships
    relationships = lookup.get_resource_relationships(card)
    print(f"\nCard relationships:")
    print(f"  Parents: {len(relationships['parents'])}")
    print(f"  Children: {len(relationships['children'])}")


def example_load_from_json():
    """Demonstrate loading from JSON file."""
    print("\n" + "=" * 60)
    print("Example 2: Loading from JSON")
    print("=" * 60)
    
    lookup = TopologyLookup()
    
    # Use correct path relative to project root
    json_file = project_root / "data" / "topology_anonymized.json"
    
    if json_file.exists():
        with open(json_file, 'r') as f:
            data = json.load(f)
            topology = data.get('topology', {})
            count = lookup.load_from_dict(topology)
        
        print(f"Loaded {count} resources from {json_file.name}")
        print(f"Resource types: {lookup.get_supported_types()}")
        
        # Example query
        elements = lookup.find_resources_by_type("FixedNetworkElement")
        print(f"\nFound {len(elements)} FixedNetworkElement resources:")
        for elem in elements:
            print(f"  - {elem.name} (ID: {elem.resId})")
    else:
        print(f"JSON file not found: {json_file}")


def example_relationship_traversal():
    """Demonstrate relationship traversal."""
    print("\n" + "=" * 60)
    print("Example 3: Relationship Traversal")
    print("=" * 60)
    
    lookup = TopologyLookup()
    
    # Create a chain: Element -> Card -> LTP
    lookup.add_resource(
        "FixedNetworkElement",
        "ne1",
        "BR-CityB-ACC-54"
    )
    lookup.add_resource(
        "FixedNetworkCard",
        "card1",
        "TPA2EG24 24",
        {"FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"}
    )
    lookup.add_resource(
        "FixedNetworkLTP",
        "ltp1",
        "Trail-6977",
        {
            "FixedNetworkCard.refParentCard": "TPA2EG24 24",
            "FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"
        }
    )
    
    # Traverse from LTP to Card to Element
    ltp = lookup.find_resources_by_name("Trail-6977", exact_match=True)[0]
    card = lookup.find_parent_resource(ltp, "FixedNetworkCard.refParentCard")
    element = lookup.find_parent_resource(card, "FixedNetworkElement.refParentNE")
    
    print(f"Traversal: LTP -> Card -> Element")
    print(f"  {ltp.name} -> {card.name} -> {element.name}")


def main():
    """Run all examples."""
    print("\nICT-RCA TopologyLookup Examples\n")
    
    example_basic_usage()
    example_load_from_json()
    example_relationship_traversal()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
