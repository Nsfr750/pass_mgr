"""
API endpoints for password sharing functionality.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from datetime import datetime, timedelta
import json

from ...core.security import get_current_user
from ...core.services.sharing_service import SharingService
from ...core.database import get_db
from ...models import PasswordEntry, User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get sharing service
def get_sharing_service(db=Depends(get_db)):
    return SharingService(db)

@router.post("/shares", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_share(
    entry_id: str,
    to_email: str,
    permissions: dict,
    expires_in_days: int = 7,
    message: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    sharing_service: SharingService = Depends(get_sharing_service)
):
    """
    Create a new password share.
    
    Permissions should be a dictionary like: {"view": True, "edit": False}
    """
    try:
        # Get the password entry
        entry = await PasswordEntry.get(entry_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Password entry not found"
            )
        
        # Check if user has permission to share this entry
        if entry.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to share this password"
            )
        
        # Create the share
        share = sharing_service.create_share(
            entry=entry,
            from_user=current_user.email,
            to_email=to_email,
            permissions=permissions,
            expires_in_days=expires_in_days,
            message=message
        )
        
        return {
            "status": "success",
            "data": {
                "share_id": share['share_id'],
                "access_url": share['access_url'],
                "expires_at": share['expires_at']
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/shares/me", response_model=dict)
async def get_my_shares(
    current_user: User = Depends(get_current_user),
    sharing_service: SharingService = Depends(get_sharing_service)
):
    """Get all shares for the current user (both sent and received)."""
    try:
        shares = sharing_service.get_user_shares(current_user.email)
        return {
            "status": "success",
            "data": shares
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/shares/{share_id}", response_model=dict)
async def get_share(
    share_id: str,
    current_user: User = Depends(get_current_user),
    sharing_service: SharingService = Depends(get_sharing_service)
):
    """Get details of a specific share."""
    try:
        share = sharing_service.get_share(share_id, current_user.email)
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found or access denied"
            )
        
        return {
            "status": "success",
            "data": share
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share(
    share_id: str,
    current_user: User = Depends(get_current_user),
    sharing_service: SharingService = Depends(get_sharing_service)
):
    """Revoke a password share."""
    try:
        success = sharing_service.revoke_share(
            share_id=share_id,
            user_email=current_user.email,
            reason="Revoked by owner"
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found or you don't have permission to revoke it"
            )
            
        return None
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/shares/{share_id}/request-access", status_code=status.HTTP_201_CREATED)
async def request_access(
    share_id: str,
    message: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    sharing_service: SharingService = Depends(get_sharing_service)
):
    """Request access to a password share."""
    try:
        success = sharing_service.request_access(
            share_id=share_id,
            requester_email=current_user.email,
            request_message=message
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process access request"
            )
            
        return {"status": "success", "message": "Access request submitted"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/shares/requests/{request_id}/respond", status_code=status.HTTP_200_OK)
async def respond_to_request(
    request_id: str,
    approve: bool,
    message: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    sharing_service: SharingService = Depends(get_sharing_service)
):
    """Respond to an access request (approve/reject)."""
    try:
        success = sharing_service.respond_to_request(
            request_id=request_id,
            responder_email=current_user.email,
            approve=approve,
            response_message=message
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process response to access request"
            )
            
        action = "approved" if approve else "rejected"
        return {"status": "success", "message": f"Access request {action}"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/shares/requests", response_model=dict)
async def get_access_requests(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    sharing_service: SharingService = Depends(get_sharing_service)
):
    """Get access requests for the current user's shares."""
    try:
        # Get shares created by the current user
        shares = sharing_service.get_user_shares(current_user.email)
        share_ids = [share['id'] for share in shares if share['type'] == 'sent']
        
        if not share_ids:
            return {"status": "success", "data": []}
        
        # Get access requests for these shares
        query = """
            SELECT ar.*, ps.entry_id, p.title as entry_title, p.username as entry_username
            FROM access_requests ar
            JOIN password_shares ps ON ar.share_id = ps.id
            JOIN passwords p ON ps.entry_id = p.id
            WHERE ar.share_id IN ({})
        """.format(", ".join(["?"] * len(share_ids)))
        
        params = tuple(share_ids)
        
        if status_filter:
            query += " AND ar.status = ?"
            params += (status_filter,)
            
        query += " ORDER BY ar.requested_at DESC"
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute(query, params)
        
        requests = []
        for row in cursor.fetchall():
            requests.append(dict(row))
            
        return {
            "status": "success",
            "data": requests
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
