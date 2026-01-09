"""Export 3D models to various formats."""

import struct
import json
import base64
import numpy as np


def export_to_format(
    mesh_data: dict,
    format: str,
    binary: bool = False,
) -> bytes:
    """
    Export mesh to specified format.
    
    Args:
        mesh_data: Dictionary with vertices, faces, normals
        format: 'stl', 'obj', 'gltf', or 'glb'
        binary: Whether to use binary format (for STL)
    
    Returns:
        Exported file content as bytes
    """
    vertices = np.array(mesh_data["vertices"])
    faces = np.array(mesh_data["faces"])
    normals = np.array(mesh_data.get("normals", []))
    
    if format == "stl":
        return _export_stl(vertices, faces, binary)
    elif format == "obj":
        return _export_obj(vertices, faces, normals)
    elif format == "gltf":
        return _export_gltf(vertices, faces, normals, binary=False)
    elif format == "glb":
        return _export_gltf(vertices, faces, normals, binary=True)
    else:
        raise ValueError(f"Unsupported format: {format}")


def _export_stl(
    vertices: np.ndarray,
    faces: np.ndarray,
    binary: bool = True,
) -> bytes:
    """Export to STL format."""
    if binary:
        return _export_stl_binary(vertices, faces)
    else:
        return _export_stl_ascii(vertices, faces)


def _export_stl_binary(vertices: np.ndarray, faces: np.ndarray) -> bytes:
    """Export to binary STL format."""
    num_triangles = len(faces)
    
    # Header (80 bytes) + triangle count (4 bytes)
    header = b'\x00' * 80
    data = bytearray(header)
    data.extend(struct.pack('<I', num_triangles))
    
    for face in faces:
        # Get triangle vertices
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]
        
        # Compute face normal
        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)
        norm = np.linalg.norm(normal)
        if norm > 0:
            normal = normal / norm
        
        # Write normal (3 floats)
        data.extend(struct.pack('<3f', *normal))
        
        # Write vertices (9 floats)
        data.extend(struct.pack('<3f', *v0))
        data.extend(struct.pack('<3f', *v1))
        data.extend(struct.pack('<3f', *v2))
        
        # Attribute byte count (unused, set to 0)
        data.extend(struct.pack('<H', 0))
    
    return bytes(data)


def _export_stl_ascii(vertices: np.ndarray, faces: np.ndarray) -> bytes:
    """Export to ASCII STL format."""
    lines = ["solid planebrane"]
    
    for face in faces:
        v0 = vertices[face[0]]
        v1 = vertices[face[1]]
        v2 = vertices[face[2]]
        
        # Compute normal
        edge1 = v1 - v0
        edge2 = v2 - v0
        normal = np.cross(edge1, edge2)
        norm = np.linalg.norm(normal)
        if norm > 0:
            normal = normal / norm
        
        lines.append(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}")
        lines.append("    outer loop")
        lines.append(f"      vertex {v0[0]:.6f} {v0[1]:.6f} {v0[2]:.6f}")
        lines.append(f"      vertex {v1[0]:.6f} {v1[1]:.6f} {v1[2]:.6f}")
        lines.append(f"      vertex {v2[0]:.6f} {v2[1]:.6f} {v2[2]:.6f}")
        lines.append("    endloop")
        lines.append("  endfacet")
    
    lines.append("endsolid planebrane")
    
    return "\n".join(lines).encode('utf-8')


def _export_obj(
    vertices: np.ndarray,
    faces: np.ndarray,
    normals: np.ndarray,
) -> bytes:
    """Export to OBJ format."""
    lines = ["# PlaneBrane OBJ Export", "# https://planebrane.example.com", ""]
    
    # Write vertices
    for v in vertices:
        lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
    
    lines.append("")
    
    # Write normals if available
    if len(normals) > 0:
        for n in normals:
            lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
        lines.append("")
    
    # Write faces (OBJ uses 1-based indexing)
    if len(normals) > 0:
        for f in faces:
            # f v1//n1 v2//n2 v3//n3
            lines.append(f"f {f[0]+1}//{f[0]+1} {f[1]+1}//{f[1]+1} {f[2]+1}//{f[2]+1}")
    else:
        for f in faces:
            lines.append(f"f {f[0]+1} {f[1]+1} {f[2]+1}")
    
    return "\n".join(lines).encode('utf-8')


def _export_gltf(
    vertices: np.ndarray,
    faces: np.ndarray,
    normals: np.ndarray,
    binary: bool = False,
) -> bytes:
    """Export to glTF 2.0 format."""
    # Convert to proper dtypes
    vertices = vertices.astype(np.float32)
    indices = faces.flatten().astype(np.uint32)
    
    if len(normals) > 0:
        normals = normals.astype(np.float32)
    
    # Create buffers
    vertex_data = vertices.tobytes()
    index_data = indices.tobytes()
    normal_data = normals.tobytes() if len(normals) > 0 else b''
    
    # Compute bounds
    v_min = vertices.min(axis=0).tolist()
    v_max = vertices.max(axis=0).tolist()
    
    # Buffer views and accessors
    buffer_views = []
    accessors = []
    
    # Index buffer view
    buffer_views.append({
        "buffer": 0,
        "byteOffset": 0,
        "byteLength": len(index_data),
        "target": 34963,  # ELEMENT_ARRAY_BUFFER
    })
    accessors.append({
        "bufferView": 0,
        "componentType": 5125,  # UNSIGNED_INT
        "count": len(indices),
        "type": "SCALAR",
    })
    
    # Vertex buffer view
    vertex_offset = len(index_data)
    buffer_views.append({
        "buffer": 0,
        "byteOffset": vertex_offset,
        "byteLength": len(vertex_data),
        "target": 34962,  # ARRAY_BUFFER
        "byteStride": 12,  # 3 * float32
    })
    accessors.append({
        "bufferView": 1,
        "componentType": 5126,  # FLOAT
        "count": len(vertices),
        "type": "VEC3",
        "min": v_min,
        "max": v_max,
    })
    
    # Normal buffer view
    primitive_attributes = {"POSITION": 1}
    
    if len(normal_data) > 0:
        normal_offset = vertex_offset + len(vertex_data)
        buffer_views.append({
            "buffer": 0,
            "byteOffset": normal_offset,
            "byteLength": len(normal_data),
            "target": 34962,
            "byteStride": 12,
        })
        accessors.append({
            "bufferView": 2,
            "componentType": 5126,
            "count": len(normals),
            "type": "VEC3",
        })
        primitive_attributes["NORMAL"] = 2
    
    # Combine buffer data
    all_buffer_data = index_data + vertex_data + normal_data
    
    # Create glTF structure
    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "PlaneBrane"
        },
        "buffers": [{
            "byteLength": len(all_buffer_data),
        }],
        "bufferViews": buffer_views,
        "accessors": accessors,
        "meshes": [{
            "primitives": [{
                "attributes": primitive_attributes,
                "indices": 0,
                "mode": 4,  # TRIANGLES
            }]
        }],
        "nodes": [{"mesh": 0}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
    }
    
    if binary:
        # GLB format
        return _create_glb(gltf, all_buffer_data)
    else:
        # glTF with embedded base64 buffer
        gltf["buffers"][0]["uri"] = (
            "data:application/octet-stream;base64," +
            base64.b64encode(all_buffer_data).decode('ascii')
        )
        return json.dumps(gltf, indent=2).encode('utf-8')


def _create_glb(gltf: dict, buffer_data: bytes) -> bytes:
    """Create GLB binary container."""
    # JSON chunk
    json_str = json.dumps(gltf)
    json_bytes = json_str.encode('utf-8')
    
    # Pad JSON to 4-byte boundary
    json_padding = (4 - (len(json_bytes) % 4)) % 4
    json_bytes += b' ' * json_padding
    
    # Pad buffer to 4-byte boundary
    buffer_padding = (4 - (len(buffer_data) % 4)) % 4
    buffer_data += b'\x00' * buffer_padding
    
    # GLB structure
    glb = bytearray()
    
    # Header: magic, version, length
    total_length = 12 + 8 + len(json_bytes) + 8 + len(buffer_data)
    glb.extend(struct.pack('<I', 0x46546C67))  # 'glTF'
    glb.extend(struct.pack('<I', 2))  # version
    glb.extend(struct.pack('<I', total_length))
    
    # JSON chunk header
    glb.extend(struct.pack('<I', len(json_bytes)))
    glb.extend(struct.pack('<I', 0x4E4F534A))  # 'JSON'
    glb.extend(json_bytes)
    
    # Buffer chunk header
    glb.extend(struct.pack('<I', len(buffer_data)))
    glb.extend(struct.pack('<I', 0x004E4942))  # 'BIN\0'
    glb.extend(buffer_data)
    
    return bytes(glb)
