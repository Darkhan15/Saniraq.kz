from fastapi import FastAPI, HTTPException, Depends, Response, Form, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from .database import SessionLocal, Base, engine
from .actions import UsersRepository, AdsRepository, CommentsRepository, FavAdsRepository
from .schemas import (
    UserCreate,
    UserUpdate,
    AdCreate,
    CommentCreate,
    CommentUpdate
)


app = FastAPI()
users_repository = UsersRepository()
ads_repository = AdsRepository()
comments_repository = CommentsRepository()
favs_repository = FavAdsRepository()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def index():
    return Response("Saniraq.kz", status_code=200)




@app.get("/auth/users")
def get_signup(db: Session = Depends(get_db)):
    all_users = users_repository.get_all(db)
    return all_users

@app.post("/auth/users")
def post_signup(
    new_user: UserCreate,
    db: Session = Depends(get_db)
):
    user_exists = users_repository.get_by_username(db=db, user_username=new_user.username)

    if user_exists:
        raise HTTPException(status_code=400, detail="User with this username already exists")
    
    users_repository.save_user(db=db, user=new_user)
    return Response("User is registred", status_code=200)




def create_jwt_token(user_id: int) -> str:
    body = {"user_id": user_id}
    token = jwt.encode(body, "kek", "HS256")
    return token

@app.post("/auth/users/login")
def post_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user_exists = users_repository.get_by_username(db, username)

    if not user_exists:
        return HTTPException(status_code=404, detail="User does not exists with this phone number")
    
    if user_exists.password != password:
        return HTTPException(status_code=400, detail="Password dont match")
    
    token = create_jwt_token(user_exists.id)
    return {"access_token": token}




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/users/login")

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        data = jwt.decode(token, "kek", "HS256")
        return data["user_id"]
    except jwt.InvalidTokenError:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid or expired token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.patch("/auth/users/me")
def patch_update_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user_id = Depends(verify_token)
):
    
    updated_user = users_repository.update_user(db, user_id=current_user_id, new_info=user_update)
    
    if not updated_user:
        raise HTTPException(status_code=400, detail="Update did not happen")
    
    return Response("Updated - OK", status_code=200)




@app.get("/auth/users/me")
def get_user_info(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    current_user_info = users_repository.get_by_id(db=db, user_id=current_user_id)

    return current_user_info




@app.post("/shanyraks")
def post_ad(
    input_ad: AdCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    saved_ad = ads_repository.save_ad(db=db, ad=input_ad, user_id=current_user_id)
    return {"ad_id": saved_ad.id}



@app.get("/shanyraks/{id}")
def get_ad(id: int, db: Session = Depends(get_db)):
    
    current_ad = ads_repository.get_by_id(db=db, ad_id=id)

    if not current_ad:  
        raise HTTPException(status_code=404, detail="Not found ad")
    
    total_comments = comments_repository.get_all_by_ad_id(db=db, ad_id=current_ad.id)
    
    return {
        "current_ad": current_ad,
        "total_comments": len(total_comments)
    }




@app.patch("/shanyraks/{id}")
def patch_update_ad(
    id: int,
    ad_update: AdCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    current_ad = ads_repository.get_by_id(db=db, ad_id=id)

    if not current_ad:
        raise HTTPException(status_code=404, detail="Not found ad")
    
    current_ad_owner_id = current_ad.user_id

    if current_ad_owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete other users' comments"
        )
    
    ads_repository.update_ad(db=db, ad_id=current_ad.id, new_info=ad_update)
    return Response("Updated - OK", status_code=200)




@app.delete("/shanyraks/{id}")
def delete_ad(
    id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    current_ad = ads_repository.get_by_id(db, ad_id=id)

    if not current_ad:
        raise HTTPException(status_code=404, detail="Not found ad")
    
    current_ad_owner_id = current_ad.user_id

    if current_ad_owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete other users' comments"
        )

    deleted_ad = ads_repository.delete_ad(db=db, ad_id=current_ad.id)

    if not deleted_ad:
        raise HTTPException(status_code=400, detail="Deletion did not happen")
    
    return Response("Deleted - OK", status_code=200)




@app.post("/shanyraks/{id}/comments")
def post_comments(
    id: int,
    new_comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    current_ad = ads_repository.get_by_id(db=db, ad_id=id)

    if not current_ad:
        raise HTTPException(status_code=404, detail="Not found ad")

    comments_repository.save_comment(db=db, comment=new_comment, user_id=current_user_id, ad_id=current_ad.id)
    return Response("Comment created - OK", status_code=200)




@app.get("/shanyraks/{id}/comments")
def get_comments(
    id: int,
    db: Session = Depends(get_db)
):
    current_ad = ads_repository.get_by_id(db=db, ad_id=id)

    if not current_ad:
            raise HTTPException(status_code=404, detail="Not found ad")
    
    all_comment_by_ad_id = comments_repository.get_all_by_ad_id(db=db, ad_id=current_ad.id)

    return {"comments": all_comment_by_ad_id}




@app.patch("/shanyraks/{id}/comments/{comment_id}")
def patch_update_comments(
    id: int,
    comment_id: int,
    new_info: CommentUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    current_ad = ads_repository.get_by_id(db=db, ad_id=id)
    current_comment = comments_repository.get_by_id(db=db, comment_id=comment_id)

    if not current_ad or not current_comment:
        raise HTTPException(status_code=404, detail="Not found")
    
    current_ad_owner_id = current_ad.user_id

    if current_ad_owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to modify other users' comments"
        )
    
    comments_repository.update_comment(db=db, comment_id=current_comment.id, new_info=new_info)
    return Response("Updated - OK", status_code=200)




@app.delete("/shanyraks/{id}/comments/{comment_id}")
def delete_comment(
    id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    current_ad = ads_repository.get_by_id(db=db, ad_id=id)
    current_comment = comments_repository.get_by_id(db=db, comment_id=comment_id)

    if not current_ad or not current_comment:
        raise HTTPException(status_code=404, detail="Not found")
    
    current_ad_owner_id = current_ad.user_id

    if current_ad_owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete other users' comments"
        )
    
    comments_repository.delete_comment(db=db, comment_id=current_comment.id)
    return Response("Deleted - OK", status_code=200)




@app.post("/auth/users/favorites/shanyraks/{id}")
def post_favorite_ads(
    id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    current_ad = ads_repository.get_by_id(db=db, ad_id=id)
    if not current_ad:
        raise HTTPException(status_code=404, detail="Not found ad")
    
    favs_repository.save_ad(db=db, ad_id=current_ad.id, fav_adress=current_ad.adress)
    return Response("Saved fav ad - OK", status_code=200)




@app.get("/auth/users/favorites/shanyraks")
def get_favs(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    shanyraks = favs_repository.get_all(db=db)
    return {"shanyraks": shanyraks}




@app.delete("/auth/users/favorites/shanyraks/{id}")
def delete_fav_ad(
    id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_token)
):
    current_fav_ad = favs_repository.get_by_id(db=db, fav_ad_id=id)

    if not current_fav_ad:
        raise HTTPException(status_code=400, detail="Not found fav ad")
    
    favs_repository.delete_ad(db=db, fav_ad_id=current_fav_ad.id)
    return Response("Deleted fav ad - OK", status_code=200)




@app.get("/shanyraks")
def get(
    limit: int,
    offset: int,
    type: str = "",
    rooms_count: int = None,
    price_from: float = None,
    price_until: float = None,
    db: Session = Depends(get_db)
):
    total_data, filtered_data = ads_repository.search(
        db=db,
        limit=limit,
        offset=offset,
        type=type,
        rooms_count=rooms_count,
        price_from=price_from,
        price_until=price_until
    )

    return {
            "total": len(total_data),
            "objects": filtered_data[::-1]
    }
