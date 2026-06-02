#!/usr/bin/env python3
"""
Convert topology_anonymized.md to JSON format.

This script parses the markdown file containing topology tables and converts
them into a structured JSON format for easier programmatic access.
"""

import json
import re
from pathlib import Path


def parse_markdown_table(table_text: str) -> list[dict]:
    """Parse a markdown table into a list of dictionaries."""
    lines = table_text.strip().split('\n')
    
    if len(lines) < 3:
        return []
    
    # Extract header line (first line after | separators)
    header_line = lines[0]
    headers = [h.strip() for h in header_line.split('|')[1:-1]]
    
    # Skip separator line (second line with ---)
    data_lines = lines[2:]
    
    records = []
    for line in data_lines:
        if not line.strip():
            continue
        
        # Split by | and clean up
        values = [v.strip() for v in line.split('|')[1:-1]]
        
        # Create dictionary mapping headers to values
        record = {}
        for i, header in enumerate(headers):
            if i < len(values):
                record[header] = values[i]
            else:
                record[header] = ""
        
        if record:  # Only add non-empty records
            records.append(record)
    
    return records


def parse_topology_markdown(file_path: str) -> dict:
    """Parse the entire topology markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by resource type headers (## ResourceType)
    sections = re.split(r'\n##\s+', content)
    
    topology_data = {}
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # First line is the resource type name
        lines = section.split('\n')
        resource_type = lines[0].strip()
        
        # Clean up resource type name (remove any leading ## that might remain)
        resource_type = re.sub(r'^#+\s*', '', resource_type).strip()
        
        # Find the table in the section
        table_start = None
        table_end = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith('|'):
                if table_start is None:
                    table_start = i
                table_end = i
        
        if table_start is not None and table_end is not None:
            table_text = '\n'.join(lines[table_start:table_end + 1])
            records = parse_markdown_table(table_text)
            topology_data[resource_type] = records
        else:
            topology_data[resource_type] = []
    
    return topology_data


def convert_to_json(input_file: str, output_file: str) -> dict:
    """Convert markdown topology file to JSON and save it."""
    # Parse the markdown file
    topology_data = parse_topology_markdown(input_file)
    
    # Create structured output
    output = {
        "metadata": {
            "source_file": input_file,
            "resource_types": list(topology_data.keys()),
            "total_resources": sum(len(resources) for resources in topology_data.values())
        },
        "topology": topology_data
    }
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully converted {input_file} to {output_file}")
    print(f"Resource types found: {len(topology_data)}")
    for resource_type, resources in topology_data.items():
        print(f"  - {resource_type}: {len(resources)} records")
    print(f"Total resources: {output['metadata']['total_resources']}")
    
    return output


def main():
    """Main entry point."""
    input_file = Path(__file__).parent / "topology_anonymized.md"
    output_file = Path(__file__).parent / "topology_anonymized.json"
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return 1
    
    convert_to_json(str(input_file), str(output_file))
    return 0


if __name__ == "__main__":
    exit(main())
