from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import (
    Priority,
    Product,
    ProductModule,
    Role,
    SLAConfiguration,
    TicketCategory,
    User,
)
from app.schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    ModuleCreate,
    ModuleRead,
    ModuleUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    SLAConfigurationRead,
    SLAConfigurationUpdate,
)


router = APIRouter(prefix="/catalog", tags=["Configuration"])


def _commit_unique(db: Session, duplicate_message: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=duplicate_message)


@router.get("/products", response_model=list[ProductRead])
def list_products(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Product]:
    if current_user.role == Role.CLIENT:
        active_only = True
    query = select(Product)
    if active_only:
        query = query.where(Product.is_active == true())
    return list(db.scalars(query.order_by(Product.name)).all())


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
) -> Product:
    product = Product(**payload.model_dump())
    db.add(product)
    _commit_unique(db, "A product with this name already exists")
    db.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    _commit_unique(db, "A product with this name already exists")
    db.refresh(product)
    return product


@router.get("/modules", response_model=list[ModuleRead])
def list_modules(
    product_id: int | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProductModule]:
    if current_user.role == Role.CLIENT:
        active_only = True
    query = select(ProductModule)
    if product_id is not None:
        query = query.where(ProductModule.product_id == product_id)
    if active_only:
        query = query.join(Product, ProductModule.product_id == Product.id).where(
            ProductModule.is_active == true(), Product.is_active == true()
        )
    return list(db.scalars(query.order_by(ProductModule.name)).all())


@router.post("/modules", response_model=ModuleRead, status_code=status.HTTP_201_CREATED)
def create_module(
    payload: ModuleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
) -> ProductModule:
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Product not found")
    module = ProductModule(**payload.model_dump())
    db.add(module)
    _commit_unique(db, "This module already exists for the product")
    db.refresh(module)
    return module


@router.patch("/modules/{module_id}", response_model=ModuleRead)
def update_module(
    module_id: int,
    payload: ModuleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
) -> ProductModule:
    module = db.get(ProductModule, module_id)
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(module, field, value)
    _commit_unique(db, "This module already exists for the product")
    db.refresh(module)
    return module


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TicketCategory]:
    if current_user.role == Role.CLIENT:
        active_only = True
    query = select(TicketCategory)
    if active_only:
        query = query.where(TicketCategory.is_active == true())
    return list(db.scalars(query.order_by(TicketCategory.name)).all())


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
) -> TicketCategory:
    category = TicketCategory(**payload.model_dump())
    db.add(category)
    _commit_unique(db, "A category with this name already exists")
    db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
) -> TicketCategory:
    category = db.get(TicketCategory, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    _commit_unique(db, "A category with this name already exists")
    db.refresh(category)
    return category


@router.get("/sla", response_model=list[SLAConfigurationRead])
def list_sla_configurations(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN, Role.MANAGER, Role.AGENT)),
) -> list[SLAConfiguration]:
    return list(db.scalars(select(SLAConfiguration).order_by(SLAConfiguration.id)).all())


@router.put("/sla/{priority}", response_model=SLAConfigurationRead)
def upsert_sla_configuration(
    priority: Priority,
    payload: SLAConfigurationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
) -> SLAConfiguration:
    configuration = db.scalar(
        select(SLAConfiguration).where(SLAConfiguration.priority == priority)
    )
    if configuration is None:
        configuration = SLAConfiguration(priority=priority, **payload.model_dump())
        db.add(configuration)
    else:
        for field, value in payload.model_dump().items():
            setattr(configuration, field, value)
    db.commit()
    db.refresh(configuration)
    return configuration
