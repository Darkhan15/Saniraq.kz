from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from .models import User, Ad, Comment, FavAd
from .schemas import (
    UserCreate,
    UserUpdate,
    AdCreate,
    CommentCreate,
    CommentUpdate
)


class UsersRepository:

    def get_all(self, db: Session, skip: int = 0, limit: int = 10):
        return db.query(User).offset(skip).limit(limit).all()
    
    def get_by_username(self, db: Session, user_username: str):
        return db.query(User).filter(User.username == user_username).first()
    
    def get_by_id(self, db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    def save_user(self, db: Session, user: UserCreate):
        db_user = User(**user.model_dump())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def update_user(self, db: Session, user_id: int, new_info: UserUpdate):
        db_user = db.query(User).filter(User.id == user_id).first()
        db_user.name = new_info.name
        db_user.city = new_info.city
        db_user.phone = new_info.phone
        db.commit()
        return True
    

class AdsRepository:

    def get_all(self, db: Session, skip: int = 0, limit: int = 10):
        return db.query(Ad).offset(skip).limit(limit).all()
    
    def get_by_id(self, db: Session, ad_id: int):
        return db.query(Ad).filter(Ad.id == ad_id).first()

    def save_ad(self, db: Session, ad: AdCreate, user_id: int):
        db_ad = Ad(**ad.model_dump(), user_id=user_id)
        db.add(db_ad)
        db.commit()
        db.refresh(db_ad)
        return db_ad
    
    def update_ad(self, db: Session, ad_id: int, new_info: AdCreate):
        db_ad = db.query(Ad).filter(Ad.id == ad_id).first()
        db_ad.type = new_info.type
        db_ad.price = new_info.price
        db_ad.adress = new_info.adress
        db_ad.area = new_info.area
        db_ad.rooms_count = new_info.rooms_count
        db_ad.description = new_info.description
        db.commit()
        return True
    
    def delete_ad(self, db: Session, ad_id: int):
        db_ad = db.query(Ad).filter(Ad.id == ad_id).first()
        db.delete(db_ad)
        db.commit()
        return True
    
    def search(
            self,
            db: Session,
            limit: int,
            offset: int,
            type: str,
            rooms_count: int,
            price_from: float,
            price_until: float,
        ):
            query = db.query(Ad)

            if type:
                query = query.filter(Ad.type == type)

            if rooms_count:
                query = query.filter(Ad.rooms_count == rooms_count)

            if price_from:
                query = query.filter(Ad.price >= price_from)

            if price_until:
                query = query.filter(Ad.price <= price_until)

            before_filter_data = query.all()
            after_filter_data = query.offset(offset).limit(limit).all()

            return before_filter_data, after_filter_data
    
class CommentsRepository:

    def get_all(self, db: Session, skip: int = 0, limit: int = 10):
        return db.query(Comment).offset(skip).limit(limit).all()
    
    def get_all_by_ad_id(self, db: Session, ad_id: int):
        return db.query(Comment).filter(Comment.ad_id == ad_id).all()
    
    def get_by_id(self, db: Session, comment_id: int):
        return db.query(Comment).filter(Comment.id == comment_id).first()
    
    def save_comment(self, db: Session, comment: CommentCreate, user_id: int, ad_id: int):
        db_comment = Comment(**comment.model_dump(), author_id = user_id, ad_id = ad_id)
        db.add(db_comment)
        db.commit()
        db.refresh(db_comment)
        return db_comment
    
    def update_comment(self, db: Session, comment_id: int, new_info: CommentUpdate):
        db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
        db_comment.content = new_info.content
        db.commit()
        return True
    
    def delete_comment(self, db: Session, comment_id: int):
        db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
        db.delete(db_comment)
        db.commit()
        return True
    
class FavAdsRepository:

    def get_all(self, db: Session, skip: int = 0, limit: int = 10):
        return db.query(FavAd).offset(skip).limit(limit).all()
    
    def get_by_id(self, db: Session, fav_ad_id: int):
        return db.query(FavAd).filter(FavAd.id == fav_ad_id).first()

    def save_ad(self, db: Session, ad_id: int, fav_adress: str):
        db_fav_ad = FavAd(ad_id = ad_id, fav_adress = fav_adress)
        db.add(db_fav_ad)
        db.commit()
        db.refresh(db_fav_ad)
        return db_fav_ad
    
    def delete_ad(self, db: Session, fav_ad_id: int):
        db_fav_ad = db.query(FavAd).filter(FavAd.id == fav_ad_id).first()
        db.delete(db_fav_ad)
        db.commit()
        return True