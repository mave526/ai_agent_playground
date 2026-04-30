"""
Authentication API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.models.user import UserCreate, TokenResponse, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.core.security import decode_token
from app.core.database import Database, Collections
from bson import ObjectId


router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency to get current user ID from access token."""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    return user_id


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    
    Returns access and refresh tokens.
    """
    try:
        return await AuthService.register_user(user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with email and password.
    
    Use form data with:
    - username: email address
    - password: user password
    """
    try:
        return await AuthService.login_user(form_data.username, form_data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
    try:
        return await AuthService.refresh_access_token(request.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout")
async def logout(
    user_id: str = Depends(get_current_user_id),
    refresh_token: RefreshTokenRequest = None
):
    """
    Logout current user.
    """
    if refresh_token:
        await AuthService.logout_user(user_id, refresh_token.refresh_token)
    
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_id)):
    """
    Get current authenticated user information.
    """
    user = await AuthService.get_current_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert ObjectId to string
    user["_id"] = str(user["_id"])
    
    # Remove sensitive data
    user.pop("password_hash", None)
    
    return user