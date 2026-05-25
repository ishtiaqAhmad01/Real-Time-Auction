from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

# ==========================
# USER SCHEMAS
# ==========================
class UserCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime
    profile_image_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ==========================
# BID SCHEMAS
# ==========================
class BidCreate(BaseModel):
    auction_id: int
    amount: Decimal = Field(gt=0)

class BidResponse(BaseModel):
    id: int
    auction_id: int
    bidder_id: int
    amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================
# Auction SCHEMAS
# ==========================

class AuctionCreate(BaseModel):
    title : str
    description : str
    starting_price : Decimal
    end_time : datetime


class AuctionResponse(BaseModel):
    id : int
    title : str
    description : str
    starting_price : Decimal
    end_time : datetime
    seller_id : int
    created_at : datetime


    model_config = ConfigDict(from_attributes=True)