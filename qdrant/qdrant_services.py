
from typing import List
from qdrant_client.models import Distance, VectorParams, PointStruct, ScoredPoint

from qdrant_client import QdrantClient

client = QdrantClient(url="http://10.66.68.17:6333")

def create_collection(collection_name: str, vector_size: int, distance=Distance.DOT):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=distance),
    )

def delete_collection(collection_name: str):
    """
    Deletes a collection from Qdrant.
    """
    client.delete_collection(collection_name=collection_name)
    print(f"Collection '{collection_name}' deleted.")

def get_collection(collection_name: str):
    """
    Retrieves the collection information from Qdrant.
    """
    collection_info = client.get_collection(collection_name=collection_name)
    return collection_info

def check_collection_exists(collection_name: str) -> bool:
    """
    Checks if a collection exists in Qdrant.
    """
    try:
        client.get_collection(collection_name=collection_name)
        return True
    except Exception as e:
        print(f"Collection '{collection_name}' does not exist: {e}")
        return False

def insert_vectors(collection_name: str, points: list):
    """
    points: list of PointStruct objects
    """
    return client.upsert(
        collection_name=collection_name,
        wait=True,
        points=points,
    )

def insert_vector(collection_name: str, point: PointStruct):
    """
    Inserts a single vector into the specified collection.
    """
    return client.upsert(
        collection_name=collection_name,
        wait=True,
        points=[point],
    )

def get_vector(collection_name: str, point_id: int):
    """
    Retrieves a vector by its ID from the specified collection.
    """
    result = client.get_point(
        collection_name=collection_name,
        point_id=point_id
    )
    return result.point if result else None

def delete_vector(collection_name: str, point_id: int):
    """
    Deletes a vector by its ID from the specified collection.
    """
    client.delete_points(
        collection_name=collection_name,
        points_selector={"ids": [point_id]}
    )
    print(f"Point with ID {point_id} deleted from collection '{collection_name}'.")

def query_collection(collection_name: str, query_vector: list, limit: int = 3, with_payload: bool = False):
    result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        with_payload=with_payload,
        limit=limit
    )
    return result.points

def search(collection_name: str, vector: list, limit: int = 3, with_payload: bool = False) -> List[ScoredPoint]:
    """
    Searches for vectors in the specified collection.
    """
    result = client.search(
        collection_name=collection_name,
        query_vector=vector,
        limit=limit,
        with_payload=with_payload
    )
    return result


# if __name__ == "__main__":
#     create_collection("test_collection", 4)
#     insert_vectors(
#         "test_collection",
#         [
#             PointStruct(id=1, vector=[0.05, 0.61, 0.76, 0.74], payload={"city": "Berlin"}),
#             PointStruct(id=2, vector=[0.19, 0.81, 0.75, 0.11], payload={"city": "London"}),
#             PointStruct(id=3, vector=[0.36, 0.55, 0.47, 0.94], payload={"city": "Moscow"}),
#             PointStruct(id=4, vector=[0.18, 0.01, 0.85, 0.80], payload={"city": "New York"}),
#             PointStruct(id=5, vector=[0.24, 0.18, 0.22, 0.44], payload={"city": "Beijing"}),
#             PointStruct(id=6, vector=[0.35, 0.08, 0.11, 0.44], payload={"city": "Mumbai"}),
#         ]
#     )
#     results = query_collection("test_collection", [0.2, 0.1, 0.9, 0.7])
#     print(results)