import io
import tempfile
import re
import pandas as pd
import xml.etree.ElementTree as ET
from fastapi import UploadFile, HTTPException
from typing import List, Dict, Any

def get_spooled_stream(file_payload: UploadFile) -> io.BytesIO:
    """
    Safely reads chunks from the UploadFile stream into an in-memory BytesIO buffer,
    leveraging the backend spooler to prevent container RAM exhaustion.
    """
    try:
        stream_buffer = io.BytesIO()
        # Read in 1MB chunks
        while True:
            chunk = file_payload.file.read(1024 * 1024)
            if not chunk:
                break
            stream_buffer.write(chunk)
        stream_buffer.seek(0)
        return stream_buffer
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to spool file payload stream: {str(exc)}"
        )

def strip_ns(tag: str) -> str:
    """Helper to remove XML namespace prefix from tags."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag

def flatten_xml_element(element: ET.Element, parent_path: str = "") -> Dict[str, str]:
    """
    Recursively flattens an XML element into a key-value flat structure.
    Integrates attributes (e.g. <value type="tax">12</value> becomes value_tax: "12")
    and prevents collisions by building fully-qualified tag paths.
    """
    flat_data = {}
    tag_name = strip_ns(element.tag)
    current_path = f"{parent_path}_{tag_name}" if parent_path else tag_name

    # Handle attributes
    attrs = element.attrib
    attr_suffix = ""
    if attrs:
        # If there's a type or key attribute, use its value as a naming modifier
        attr_vals = [str(v) for k, v in attrs.items() if k.lower() in ["type", "key", "id", "name"]]
        if attr_vals:
            attr_suffix = f"_{'_'.join(attr_vals)}"
            attr_suffix = re.sub(r'[^a-zA-Z0-9_]', '_', attr_suffix)

    # Process child nodes or text value
    children = list(element)
    if not children:
        # Leaf element - extract text value
        val = (element.text or "").strip()
        key_name = f"{current_path}{attr_suffix}"
        flat_data[key_name] = val
    else:
        # Node has children, recursively flatten children
        child_counts = {}
        for child in children:
            c_tag = strip_ns(child.tag)
            child_counts[c_tag] = child_counts.get(c_tag, 0) + 1

        for child in children:
            c_tag = strip_ns(child.tag)
            child_flat = flatten_xml_element(child, current_path)
            
            # If sibling tag name is repeated and doesn't have differentiating attributes, append counter
            if child_counts[c_tag] > 1 and not any(k.lower() in ["type", "key", "id", "name"] for k in child.attrib):
                # Add counter suffix to flattened keys
                for k, v in child_flat.items():
                    flat_data[f"{k}_seq"] = v
            else:
                flat_data.update(child_flat)

    return flat_data

def parse_structured_xml_payload(stream_buffer: io.BytesIO) -> pd.DataFrame:
    """
    Parses deeply nested, namespace-heavy, and potentially attribute-differentiated XML datasets
    by finding repeating blocks (e.g., <transaction>) and flattening their hierarchies.
    """
    try:
        tree = ET.parse(stream_buffer)
        root = tree.getroot()
        
        # Strip root namespaces if present
        root_tag = strip_ns(root.tag)
        
        # Detect the repeating transactional blocks
        # We look for a common child tag that is repeated or matches 'transaction'
        records = []
        
        # Strategy 1: Find any tags matching 'transaction' or locate the most repeating direct children
        candidates = []
        for child in root:
            candidates.append(strip_ns(child.tag))
            
        if not candidates:
            # Empty XML or single node
            flat = flatten_xml_element(root)
            return pd.DataFrame([flat])
            
        # Find the most frequent tag in children
        target_tag = max(set(candidates), key=candidates.count)
        
        # Traverse and flatten targets
        for child in root:
            if strip_ns(child.tag) == target_tag or "transaction" in strip_ns(child.tag).lower():
                flat_rec = flatten_xml_element(child)
                records.append(flat_rec)
                
        if not records:
            # Fallback: search anywhere in tree for 'transaction' nodes
            for elem in root.iter():
                if "transaction" in strip_ns(elem.tag).lower():
                    flat_rec = flatten_xml_element(elem)
                    records.append(flat_rec)
                    
        if not records:
            # Absolute fallback: just flatten direct children
            for child in root:
                records.append(flatten_xml_element(child))
                
        df = pd.DataFrame(records)
        return df.fillna("")
    except Exception as exc:
        raise ValueError(f"XML Parsing Exception: {str(exc)}")

def parse_incoming_file_stream(file_payload: UploadFile) -> pd.DataFrame:
    """
    Decodes and normalizes file payloads from stream buffers based on file extensions
    to construct a uniform, typed, and clean Pandas DataFrame.
    """
    filename = file_payload.filename
    extension = filename.split(".")[-1].lower() if "." in filename else ""
    
    # Obtain safe spooled stream
    stream_buffer = get_spooled_stream(file_payload)
    
    try:
        if extension == "csv":
            # read csv keeping all fields as strings initially to preserve formatting/leading zeros
            return pd.read_csv(stream_buffer, dtype=str, keep_default_na=False)
            
        elif extension in ["xlsx", "xls"]:
            # read Excel keeping all fields as strings initially
            return pd.read_excel(stream_buffer, dtype=str, keep_default_na=False)
            
        elif extension == "xml":
            return parse_structured_xml_payload(stream_buffer)
            
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"The file extension '{extension}' is not supported by the ingestion pipeline."
            )
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise exc
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process file stream for {filename}: {str(exc)}"
        )
