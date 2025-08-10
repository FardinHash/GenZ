from fastapi import APIRouter

router = APIRouter()


@router.post("")
async def create_key():
    return {"detail": "create key not implemented"}


@router.get("")
async def list_keys():
    return {"detail": "list keys not implemented"}


@router.delete("/{key_id}")
async def delete_key(key_id: str):
    return {"detail": f"delete key {key_id} not implemented"} 