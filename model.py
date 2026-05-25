from sqlalchemy import Column, String, Integer, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass


# ===========================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True))
    profile_image_path = Column(String)

    # Relationships
    auctions = relationship("Auction", back_populates="seller")
    bids = relationship("Bid", back_populates="user")

    def __repr__(self):
        return f"{self.first_name} {self.last_name}"

# ===========================================

class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    starting_price = Column(Numeric(10, 2))
    seller_id = Column(Integer, ForeignKey("users.id"))
    end_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True))
    
    # Relationships
    seller = relationship("User", back_populates="auctions")
    images = relationship("ItemImage", back_populates="auction")
    bids = relationship("Bid", back_populates="item")

    def __repr__(self):
        return f"{self.title} | {self.starting_price}"

# ===========================================

class ItemImage(Base):
    __tablename__ = 'item_images'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('auctions.id'))
    file_path = Column(String, nullable=False)
    
    # Relationships
    auction = relationship("Auction", back_populates="images")

# ===========================================

class Bid(Base):
    __tablename__ = "bids"
    
    id = Column(Integer, primary_key=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"))
    bidder_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    user = relationship("User", back_populates="bids")
    item = relationship("Auction", back_populates="bids")