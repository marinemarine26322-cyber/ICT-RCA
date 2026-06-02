"""
Topology Resource Lookup Utility

This module provides a utility class for looking up relationships between
network topology resources based on the topology_anonymized.md schema.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Resource:
    """Base class for all topology resources."""
    resId: str
    name: str
    resource_type: str
    properties: Dict[str, Any] = field(default_factory=dict)


class TopologyLookup:
    """
    A utility class for performing lookups between topology resources.
    
    This class supports the following resource types:
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
    
    Supported lookup operations:
    - find_resource_by_id: Find a resource by its resId
    - find_resources_by_type: Find all resources of a given type
    - find_resources_by_name: Find resources by name (partial match supported)
    - find_child_resources: Find child resources referencing a parent
    - find_parent_resource: Find parent resource referenced by a child
    - get_resource_relationships: Get all relationships for a resource
    """
    
    SUPPORTED_RESOURCE_TYPES = [
        'FixedNetworkCard',
        'FixedNetworkElement', 
        'FixedNetworkLTP',
        'FixedNetworkLink',
        'PW',
        'PWE3Trail',
        'PWE3XC',
        'PWTrail',
        'ServiceAccessPoint',
        'TunnelHop',
        'TunnelTrail'
    ]
    
    # Mapping of reference fields to their target resource types
    REFERENCE_FIELD_MAPPING = {
        'FixedNetworkCard': {
            'FixedNetworkElement.refParentNE': 'FixedNetworkElement'
        },
        'FixedNetworkLTP': {
            'FixedNetworkCard.refParentCard': 'FixedNetworkCard',
            'FixedNetworkElement.refParentNE': 'FixedNetworkElement',
            'FixedNetworkLTP.refParentLTP': 'FixedNetworkLTP',
            'FixedNetworkLTP.refTrunkLTP': 'FixedNetworkLTP'
        },
        'FixedNetworkLink': {
            'FixedNetworkLTP.refAEndLTP': 'FixedNetworkLTP',
            'FixedNetworkLTP.refZEndLTP': 'FixedNetworkLTP'
        },
        'PW': {
            'FixedNetworkElement.refParentNE': 'FixedNetworkElement',
            'PWE3XC.refPwe3Xc': 'PWE3XC',
            'TunnelHop.refBindingTunnel': 'TunnelTrail'
        },
        'PWE3Trail': {
            'FixedNetworkElement.refAEndNE1': 'FixedNetworkElement',
            'FixedNetworkElement.refZEndNE1': 'FixedNetworkElement',
            'ServiceAccessPoint.refAEndLTP1': 'ServiceAccessPoint',
            'ServiceAccessPoint.refZEndLTP1': 'ServiceAccessPoint'
        },
        'PWE3XC': {
            'FixedNetworkElement.refParentNE': 'FixedNetworkElement',
            'PW.refZEndPWList': 'PW',
            'ServiceAccessPoint.refEndLTPList': 'ServiceAccessPoint'
        },
        'PWTrail': {
            'FixedNetworkElement.refAEndNE': 'FixedNetworkElement',
            'FixedNetworkElement.refZEndNE': 'FixedNetworkElement',
            'PW.refAEndPW': 'PW',
            'PW.refZEndPW': 'PW',
            'PWE3Trail.refPwe3Trail': 'PWE3Trail',
            'TunnelTrail.refTunnelList': 'TunnelTrail'
        },
        'ServiceAccessPoint': {
            'FixedNetworkElement.refParentNE': 'FixedNetworkElement',
            'FixedNetworkLTP.refBindingLTP': 'FixedNetworkLTP',
            'FixedNetworkLTP.refPort': 'FixedNetworkLTP',
            'PWE3Trail.SAP.refService': 'PWE3Trail'
        },
        'TunnelHop': {
            'Static.hopSequenceId': None,  # Not a reference
            'FixedNetworkElement.refParentNE': 'FixedNetworkElement',
            'FixedNetworkLTP.refAEndLTP': 'FixedNetworkLTP',
            'FixedNetworkLTP.refZEndLTP': 'FixedNetworkLTP',
            'TunnelTrail.refTunnelTrail': 'TunnelTrail'
        },
        'TunnelTrail': {
            'FixedNetworkElement.refAEndNE': 'FixedNetworkElement',
            'FixedNetworkElement.refZEndNE': 'FixedNetworkElement',
            'FixedNetworkLTP.refAEndPortNativeId': 'FixedNetworkLTP',
            'FixedNetworkLTP.refZEndPortNativeId': 'FixedNetworkLTP'
        }
    }
    
    def __init__(self):
        """Initialize the lookup utility with empty resource stores."""
        self._resources: Dict[str, Dict[str, Resource]] = {
            rt: {} for rt in self.SUPPORTED_RESOURCE_TYPES
        }
        self._name_index: Dict[str, List[Resource]] = {}
    
    def add_resource(self, resource_type: str, resId: str, name: str, 
                     properties: Optional[Dict[str, Any]] = None) -> Resource:
        """
        Add a resource to the lookup index.
        
        Args:
            resource_type: Type of the resource (must be in SUPPORTED_RESOURCE_TYPES)
            resId: Unique identifier for the resource
            name: Name of the resource
            properties: Additional properties of the resource
            
        Returns:
            The created Resource object
            
        Raises:
            ValueError: If resource_type is not supported
        """
        if resource_type not in self.SUPPORTED_RESOURCE_TYPES:
            raise ValueError(f"Unsupported resource type: {resource_type}. "
                           f"Supported types: {self.SUPPORTED_RESOURCE_TYPES}")
        
        resource = Resource(
            resId=resId,
            name=name,
            resource_type=resource_type,
            properties=properties or {}
        )
        
        self._resources[resource_type][resId] = resource
        
        # Update name index
        if name not in self._name_index:
            self._name_index[name] = []
        self._name_index[name].append(resource)
        
        return resource
    
    def load_from_dict(self, data: Dict[str, List[Dict[str, Any]]]) -> int:
        """
        Load resources from a dictionary structure.
        
        Args:
            data: Dictionary mapping resource types to lists of resource data
            
        Returns:
            Number of resources loaded
        """
        count = 0
        for resource_type, resources in data.items():
            if resource_type in self.SUPPORTED_RESOURCE_TYPES:
                for res_data in resources:
                    resId = res_data.get('resId')
                    name = res_data.get('name', '')
                    properties = {k: v for k, v in res_data.items() 
                                 if k not in ['resId', 'name']}
                    if resId:
                        self.add_resource(resource_type, resId, name, properties)
                        count += 1
        return count
    
    def find_resource_by_id(self, resId: str) -> Optional[Resource]:
        """
        Find a resource by its unique ID.
        
        Args:
            resId: The unique resource identifier
            
        Returns:
            The Resource if found, None otherwise
        """
        for resource_type in self.SUPPORTED_RESOURCE_TYPES:
            if resId in self._resources[resource_type]:
                return self._resources[resource_type][resId]
        return None
    
    def find_resource_by_id_and_type(self, resId: str, 
                                     resource_type: str) -> Optional[Resource]:
        """
        Find a resource by its ID and type.
        
        Args:
            resId: The unique resource identifier
            resource_type: The type of resource to search in
            
        Returns:
            The Resource if found, None otherwise
        """
        if resource_type not in self.SUPPORTED_RESOURCE_TYPES:
            return None
        return self._resources[resource_type].get(resId)
    
    def find_resources_by_type(self, resource_type: str) -> List[Resource]:
        """
        Find all resources of a given type.
        
        Args:
            resource_type: The type of resources to find
            
        Returns:
            List of matching resources
        """
        if resource_type not in self.SUPPORTED_RESOURCE_TYPES:
            return []
        return list(self._resources[resource_type].values())
    
    def find_resources_by_name(self, name: str, 
                               exact_match: bool = False) -> List[Resource]:
        """
        Find resources by name.
        
        Args:
            name: The name to search for
            exact_match: If True, only exact matches are returned.
                        If False, partial matches (substring) are returned.
            
        Returns:
            List of matching resources
        """
        results = []
        
        if exact_match:
            return self._name_index.get(name, [])
        
        # Partial match
        for indexed_name, resources in self._name_index.items():
            if name in indexed_name:
                results.extend(resources)
        
        return results
    
    def find_child_resources(self, parent_resource: Resource, 
                             reference_field: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find all child resources that reference the given parent resource.
        
        Args:
            parent_resource: The parent resource to find children for
            reference_field: Optional specific reference field to search.
                           If None, searches all reference fields.
                           
        Returns:
            List of dictionaries containing child resource and reference field info
        """
        results = []
        parent_type = parent_resource.resource_type
        
        # Determine which resource types can reference this parent type
        for child_type, ref_mapping in self.REFERENCE_FIELD_MAPPING.items():
            for ref_field, ref_target_type in ref_mapping.items():
                if ref_target_type == parent_type:
                    # Check if we should filter by specific reference field
                    if reference_field and ref_field != reference_field:
                        continue
                    
                    # Search for children with this reference
                    for child_res in self._resources[child_type].values():
                        ref_value = child_res.properties.get(ref_field)
                        if ref_value and ref_value == parent_resource.name:
                            results.append({
                                'child': child_res,
                                'reference_field': ref_field,
                                'reference_value': ref_value
                            })
        
        return results
    
    def find_parent_resource(self, child_resource: Resource,
                            reference_field: str) -> Optional[Resource]:
        """
        Find the parent resource referenced by a child resource.
        
        Args:
            child_resource: The child resource
            reference_field: The reference field to look up
            
        Returns:
            The parent Resource if found, None otherwise
        """
        if child_resource.resource_type not in self.REFERENCE_FIELD_MAPPING:
            return None
        
        ref_mapping = self.REFERENCE_FIELD_MAPPING[child_resource.resource_type]
        if reference_field not in ref_mapping:
            return None
        
        target_type = ref_mapping[reference_field]
        if not target_type:
            return None
        
        ref_value = child_resource.properties.get(reference_field)
        if not ref_value:
            return None
        
        # Find the resource by name in the target type
        for resource in self._resources[target_type].values():
            if resource.name == ref_value:
                return resource
        
        return None
    
    def get_resource_relationships(self, resource: Resource) -> Dict[str, Any]:
        """
        Get all relationships for a resource (both parent and child relationships).
        
        Args:
            resource: The resource to get relationships for
            
        Returns:
            Dictionary containing parents and children relationships
        """
        relationships = {
            'resource': resource,
            'parents': [],
            'children': []
        }
        
        # Find parent relationships
        if resource.resource_type in self.REFERENCE_FIELD_MAPPING:
            ref_mapping = self.REFERENCE_FIELD_MAPPING[resource.resource_type]
            for ref_field, target_type in ref_mapping.items():
                if target_type:
                    parent = self.find_parent_resource(resource, ref_field)
                    if parent:
                        relationships['parents'].append({
                            'parent': parent,
                            'reference_field': ref_field
                        })
        
        # Find child relationships
        children = self.find_child_resources(resource)
        relationships['children'] = children
        
        return relationships
    
    def get_supported_types(self) -> List[str]:
        """Return list of supported resource types."""
        return self.SUPPORTED_RESOURCE_TYPES.copy()
    
    def get_reference_fields(self, resource_type: str) -> Dict[str, str]:
        """
        Get all reference fields for a resource type.
        
        Args:
            resource_type: The resource type to get reference fields for
            
        Returns:
            Dictionary mapping reference fields to their target types
        """
        return self.REFERENCE_FIELD_MAPPING.get(resource_type, {})
    
    def clear(self):
        """Clear all loaded resources."""
        self._resources = {rt: {} for rt in self.SUPPORTED_RESOURCE_TYPES}
        self._name_index = {}
    
    def get_resource_count(self, resource_type: Optional[str] = None) -> int:
        """
        Get the count of resources.
        
        Args:
            resource_type: Optional specific type to count. 
                          If None, returns total count across all types.
                          
        Returns:
            Number of resources
        """
        if resource_type:
            if resource_type not in self.SUPPORTED_RESOURCE_TYPES:
                return 0
            return len(self._resources[resource_type])
        
        return sum(len(resources) for resources in self._resources.values())
