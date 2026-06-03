# ICT-RCA

ICT Root Cause Analysis (RCA) Tool - Topology Resource Lookup Utility.

## Project Structure

```
ict-rca/
├── README.md                 # This file
├── pyproject.toml            # Python project configuration
├── requirements.txt          # Project dependencies
├── src/                      # Source code
│   └── topology_lookup.py    # Main topology lookup utility
├── test/                     # Unit tests
│   └── test_topology_lookup.py
├── scripts/                  # Utility scripts
│   └── convert_topology_to_json.py
├── data/                     # Data files
│   ├── topology_anonymized.md
│   ├── topology_anonymized.json
│   └── api_schema.json
├── docs/                     # Documentation
│   ├── specifications.md
│   ├── ut_report.md
│   └── topology_anonymized_visualized.md
└── examples/                 # Example cases and templates
    ├── case_TPA2EG24_24_card_fault.md
    ├── case_TPA2EG24_24_card_fault.html
    ├── case_template.md
    ├── testcase_template
    └── example_usage.py      # Usage examples script
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

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
```

### Loading from JSON

```python
import json
from src.topology_lookup import TopologyLookup

lookup = TopologyLookup()

with open('data/topology_anonymized.json', 'r') as f:
    data = json.load(f)
    topology = data.get('topology', {})
    lookup.load_from_dict(topology)
```

### Running Tests

```bash
python -m pytest test/
```

Or using unittest:

```bash
python -m unittest discover -s test
```

## Supported Resource Types

- FixedNetworkCard
- FixedNetworkElement
- FixedNetworkLTP
- FixedNetworkLink
- PW
- PWE3Trail
- PWE3XC
- PWTrail
- ServiceAccessPoint
- TunnelHop
- TunnelTrail

## Documentation

See the `docs/` directory for detailed documentation:
- [Specifications](docs/specifications.md) - API specification and usage guide
- [Unit Test Report](docs/ut_report.md) - Test coverage report
- [Topology Visualization](docs/topology_anonymized_visualized.md) - Visual topology guide

## License

[Add your license here]
