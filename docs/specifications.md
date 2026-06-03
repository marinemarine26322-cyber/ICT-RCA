# Topology Resource Lookup Tool - Specifications

## 1. Overview

This document describes the specifications for the `TopologyLookup` utility class, which provides resource relationship lookup capabilities for network topology data based on the `topology_anonymized.md` schema.

## 2. Supported Resource Types

The tool supports the following 11 resource types:

| Resource Type | Description |
|--------------|-------------|
| FixedNetworkCard | Network interface cards and hardware modules |
| FixedNetworkElement | Network elements (routers, switches, etc.) |
| FixedNetworkLTP | Logical Termination Points (ports, interfaces, tunnels) |
| FixedNetworkLink | Links between LTPs |
| PW | Pseudowire connections |
| PWE3Trail | PWE3 service trails |
| PWE3XC | PWE3 cross-connects |
| PWTrail | Pseudowire trails |
| ServiceAccessPoint | Service access points |
| TunnelHop | Tunnel hop sequence entries |
| TunnelTrail | Tunnel trails |

## 3. Reference Field Mappings

The following table defines all reference fields and their target resource types:

### 3.1 FixedNetworkCard References
| Reference Field | Target Type | Description |
|----------------|-------------|-------------|
| FixedNetworkElement.refParentNE | FixedNetworkElement | Parent network element |

### 3.2 FixedNetworkLTP References
| Reference Field | Target Type | Description |
|----------------|-------------|-------------|
| FixedNetworkCard.refParentCard | FixedNetworkCard | Parent card |
| FixedNetworkElement.refParentNE | FixedNetworkElement | Parent network element |
| FixedNetworkLTP.refParentLTP | FixedNetworkLTP | Parent LTP |
| FixedNetworkLTP.refTrunkLTP | FixedNetworkLTP | Trunk LTP |

### 3.3 FixedNetworkLink References
| Reference Field | Target Type | Description |
|----------------|-------------|-------------|
| FixedNetworkLTP.refAEndLTP | FixedNetworkLTP | A-end LTP |
| FixedNetworkLTP.refZEndLTP | FixedNetworkLTP | Z-end LTP |

### 3.4 PW References
| Reference Field | Target Type | Description |
|----------------|-------------|-------------|
| FixedNetworkElement.refParentNE | FixedNetworkElement | Parent network element |
| PWE3XC.refPwe3Xc | PWE3XC | PWE3 cross-connect reference |
| TunnelHop.refBindingTunnel | TunnelTrail | Binding tunnel trail |

### 3.5 PWE3Trail References
| Reference Field | Target Type | Description |
|----------------|-------------|-------------|
| FixedNetworkElement.refAEndNE1 | FixedNetworkElement | A-end network element |
| FixedNetworkElement.refZEndNE1 | FixedNetworkElement | Z-end network element |
| ServiceAccessPoint.refAEndLTP1 | ServiceAccessPoint | A-end SAP |
| ServiceAccessPoint.refZEndLTP1 | ServiceAccessPoint | Z-end SAP |

### 3.6 PWE3XC References
| Reference Field | Target Type | Description |
|----------------|-------------|-------------|
| FixedNetworkElement.refParentNE | FixedNetworkElement | Parent network element |
| PW.refZEndPWList | PW | Z-end PW list |
| ServiceAccessPoint.refEndLTPList | ServiceAccessPoint | End LTP list |

### 3.7 PWTrail References
| Reference Field | Target Type | Description |
|----------------|-------------|-------------|
| FixedNetworkElement.refAEndNE | FixedNetworkElement | A-end network element |
| FixedNetworkElement.refZEndNE | FixedNetworkElement | Z-end network element |
| PW.refAEndPW | PW | A-end PW |
| PW.refZEndPW | PW | Z-end PW |
| PWE3Trail.refPwe3Trail | PWE3Trail | PWE3 trail reference |
| TunnelTrail.refTunnelList | TunnelTrail | Tunnel list |

### 3.8 ServiceAccessPoint References
| Reference Field | Target Type | Description |
|----------------|-------------|-------------|
| FixedNetworkElement.refParentNE | FixedNetworkElement | Parent network element |
| FixedNetworkLTP.refBindingLTP | FixedNetworkLTP | Binding LTP |
| FixedNetworkLTP.refPort | FixedNetworkLTP | Port LTP |
| PWE3Trail.SAP.refService | PWE3Trail | Service trail |

### 3.9 TunnelHop References
| Reference Field | Target Type | Description |
|----------------|-------------|-------------|
| Static.hopSequenceId | None | Hop sequence identifier (not a reference) |
| FixedNetworkElement.refParentNE | FixedNetworkElement | Parent network element |
| FixedNetworkLTP.refAEndLTP | FixedNetworkLTP | A-end LTP |
| FixedNetworkLTP.refZEndLTP | FixedNetworkLTP | Z-end LTP |
| TunnelTrail.refTunnelTrail | TunnelTrail | Tunnel trail |

### 3.10 TunnelTrail References
| Reference Field | Target Type | Description |
|----------------|-------------|-------------|
| FixedNetworkElement.refAEndNE | FixedNetworkElement | A-end network element |
| FixedNetworkElement.refZEndNE | FixedNetworkElement | Z-end network element |
| FixedNetworkLTP.refAEndPortNativeId | FixedNetworkLTP | A-end port native ID |
| FixedNetworkLTP.refZEndPortNativeId | FixedNetworkLTP | Z-end port native ID |

## 4. API Specification

### 4.1 Class: TopologyLookup

#### Constructor
```python
def __init__(self)
```
Initialize the lookup utility with empty resource stores.

#### Methods

##### add_resource
```python
def add_resource(resource_type: str, resId: str, name: str, 
                 properties: Optional[Dict[str, Any]] = None) -> Resource
```
Add a resource to the lookup index.

**Parameters:**
- `resource_type`: Type of the resource (must be in SUPPORTED_RESOURCE_TYPES)
- `resId`: Unique identifier for the resource
- `name`: Name of the resource
- `properties`: Additional properties of the resource

**Returns:** The created Resource object

**Raises:** ValueError if resource_type is not supported

---

##### load_from_dict
```python
def load_from_dict(data: Dict[str, List[Dict[str, Any]]]) -> int
```
Load resources from a dictionary structure.

**Parameters:**
- `data`: Dictionary mapping resource types to lists of resource data

**Returns:** Number of resources loaded

---

##### find_resource_by_id
```python
def find_resource_by_id(resId: str) -> Optional[Resource]
```
Find a resource by its unique ID.

**Parameters:**
- `resId`: The unique resource identifier

**Returns:** The Resource if found, None otherwise

---

##### find_resource_by_id_and_type
```python
def find_resource_by_id_and_type(resId: str, resource_type: str) -> Optional[Resource]
```
Find a resource by its ID and type.

**Parameters:**
- `resId`: The unique resource identifier
- `resource_type`: The type of resource to search in

**Returns:** The Resource if found, None otherwise

---

##### find_resources_by_type
```python
def find_resources_by_type(resource_type: str) -> List[Resource]
```
Find all resources of a given type.

**Parameters:**
- `resource_type`: The type of resources to find

**Returns:** List of matching resources

---

##### find_resources_by_name
```python
def find_resources_by_name(name: str, exact_match: bool = False) -> List[Resource]
```
Find resources by name.

**Parameters:**
- `name`: The name to search for
- `exact_match`: If True, only exact matches; if False, partial matches (substring)

**Returns:** List of matching resources

---

##### find_child_resources
```python
def find_child_resources(parent_resource: Resource, 
                         reference_field: Optional[str] = None) -> List[Dict[str, Any]]
```
Find all child resources that reference the given parent resource.

**Parameters:**
- `parent_resource`: The parent resource to find children for
- `reference_field`: Optional specific reference field to search

**Returns:** List of dictionaries containing child resource and reference field info

---

##### find_parent_resource
```python
def find_parent_resource(child_resource: Resource, reference_field: str) -> Optional[Resource]
```
Find the parent resource referenced by a child resource.

**Parameters:**
- `child_resource`: The child resource
- `reference_field`: The reference field to look up

**Returns:** The parent Resource if found, None otherwise

---

##### get_resource_relationships
```python
def get_resource_relationships(resource: Resource) -> Dict[str, Any]
```
Get all relationships for a resource (both parent and child relationships).

**Parameters:**
- `resource`: The resource to get relationships for

**Returns:** Dictionary containing 'resource', 'parents', and 'children' keys

---

##### get_supported_types
```python
def get_supported_types() -> List[str]
```
Return list of supported resource types.

---

##### get_reference_fields
```python
def get_reference_fields(resource_type: str) -> Dict[str, str]
```
Get all reference fields for a resource type.

**Parameters:**
- `resource_type`: The resource type to get reference fields for

**Returns:** Dictionary mapping reference fields to their target types

---

##### clear
```python
def clear()
```
Clear all loaded resources.

---

##### get_resource_count
```python
def get_resource_count(resource_type: Optional[str] = None) -> int
```
Get the count of resources.

**Parameters:**
- `resource_type`: Optional specific type to count. If None, returns total count.

**Returns:** Number of resources

---

### 4.2 Data Class: Resource

```python
@dataclass
class Resource:
    resId: str
    name: str
    resource_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
```

**Fields:**
- `resId`: Unique resource identifier
- `name`: Resource name
- `resource_type`: Type of the resource
- `properties`: Dictionary of additional properties including reference fields

## 5. Usage Examples

### 5.1 Basic Usage
```python
from src.topology_lookup import TopologyLookup

lookup = TopologyLookup()

# Add resources
lookup.add_resource("FixedNetworkElement", "ne1", "BR-CityB-ACC-54")
lookup.add_resource(
    "FixedNetworkCard", 
    "card1", 
    "TPA2EG24 24",
    {"FixedNetworkElement.refParentNE": "BR-CityB-ACC-54"}
)

# Find by ID
resource = lookup.find_resource_by_id("ne1")

# Find by name
resources = lookup.find_resources_by_name("CityB")

# Get parent relationship
card = lookup.find_resource_by_id("card1")
parent = lookup.find_parent_resource(card, "FixedNetworkElement.refParentNE")

# Get child relationships
element = lookup.find_resource_by_id("ne1")
children = lookup.find_child_resources(element)

# Get all relationships
relationships = lookup.get_resource_relationships(card)
```

### 5.2 Loading from Dictionary
```python
data = {
    "FixedNetworkElement": [
        {"resId": "ne1", "name": "NE1"},
        {"resId": "ne2", "name": "NE2"}
    ],
    "FixedNetworkCard": [
        {"resId": "card1", "name": "Card1", "FixedNetworkElement.refParentNE": "NE1"}
    ]
}

count = lookup.load_from_dict(data)
```

### 5.3 Relationship Traversal
```python
# Traverse from LTP to Card to Element
ltp = lookup.find_resources_by_name("Trail-6977", exact_match=True)[0]
card = lookup.find_parent_resource(ltp, "FixedNetworkCard.refParentCard")
element = lookup.find_parent_resource(card, "FixedNetworkElement.refParentNE")
print(f"LTP -> Card: {card.name} -> Element: {element.name}")
```

## 6. Test Coverage

The unit tests cover the following scenarios:

### 6.1 Resource Tests
- Resource creation with and without properties
- Resource data integrity

### 6.2 Initialization Tests
- Proper initialization of all resource type stores
- Supported types retrieval

### 6.3 Add Resource Tests
- Adding resources of each supported type
- Adding resources with properties
- Error handling for unsupported types
- Multiple resources of same/different types

### 6.4 Load From Dict Tests
- Loading valid resources
- Ignoring unsupported types
- Empty dictionary handling

### 6.5 Find By ID Tests
- Finding existing resources
- Non-existent resource handling
- Type-specific lookups
- Wrong type handling

### 6.6 Find By Type Tests
- Retrieving all resources of a type
- Unsupported type handling
- Empty type handling

### 6.7 Find By Name Tests
- Exact match searches
- Partial match searches
- No match handling
- Duplicate name handling

### 6.8 Parent/Child Relationship Tests
- Finding parent resources
- Finding child resources
- Specific reference field filtering
- Missing reference handling

### 6.9 Relationship Tests
- Getting complete relationship graphs
- Multi-level relationship traversal

### 6.10 Utility Method Tests
- Reference field retrieval
- Clear functionality
- Resource counting

### 6.11 Integration Tests
- Real-world data loading
- Complex relationship traversal
- Multi-hop parent lookups

## 7. Performance Considerations

- **Time Complexity:**
  - `find_resource_by_id`: O(1) average case
  - `find_resources_by_name`: O(n) where n is number of unique names
  - `find_child_resources`: O(m * r) where m is number of resource types and r is average references per type
  - `find_parent_resource`: O(k) where k is number of resources of target type

- **Space Complexity:**
  - O(n) where n is total number of resources
  - Additional O(m) for name index where m is number of unique names

## 8. Limitations

1. Resources are stored in-memory only; no persistence is provided
2. Reference resolution is by name matching, not by ID
3. Circular references are not detected or prevented
4. Thread safety is not guaranteed for concurrent modifications

## 9. Version Information

- **Version:** 1.0.0
- **Based on:** topology_anonymized.md schema
- **Python Version:** 3.7+
