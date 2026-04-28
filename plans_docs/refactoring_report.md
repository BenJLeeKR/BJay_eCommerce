# 리팩토링 리포트 (Refactoring Report)

> **작성일**: 2026-04-24  
> **검토 범위**: `workspace/app/` 전체 (models, schemas, routers, crud, core, database, dependencies, main)  
> **기준 문서**: `reference_docs/coding_convention.md`  
> **분류 기준**: 🔴 Critical (치명적 결함) / 🟡 Warning (권장 개선)

---

## 🔴 Critical (치명적 결함)

### C-1. 하드코딩된 시크릿 키 (보안)

- **파일**: [`workspace/app/core/config.py:30`](../workspace/app/core/config.py:30)
- **문제**: `SECRET_KEY: str = "change-me"`가 기본값으로 하드코딩되어 있습니다. 이 값은 JWT 토큰 서명에 직접 사용되며, 배포 시 변경되지 않으면 누구나 동일한 키로 유효한 JWT를 위조할 수 있습니다.
- **영향**: JWT 토큰 위조 → 인증 우회 → 전체 API 무단 접근 가능
- **AS-IS**:
  ```python
  # workspace/app/core/config.py
  SECRET_KEY: str = "change-me"
  ```
- **TO-BE**:
  ```python
  # workspace/app/core/config.py
  SECRET_KEY: str = Field(default="change-me", validation_alias="SECRET_KEY")
  # .env 파일에 SECRET_KEY=실제-랜덤-값 을 반드시 설정하도록 문서화
  ```

---

### C-2. 비밀번호 해시 누락 — 평문 비밀번호가 DB에 직접 저장됨 (보안)

- **파일**: [`workspace/app/routers/user.py:79`](../workspace/app/routers/user.py:79), [`workspace/app/routers/admin.py:79`](../workspace/app/routers/admin.py:79)
- **문제**: 회원 및 관리자 생성 API가 `payload.password_hash`를 그대로 DB에 저장합니다. 클라이언트가 보낸 값이 이미 해시되었다는 보장이 없으며, `password_hash`라는 필드명에도 불구하고 실제로는 해시 처리 없이 평문이 그대로 저장될 위험이 있습니다. [`workspace/app/core/security.py:18`](../workspace/app/core/security.py:18)에 `get_password_hash()` 함수가 이미 구현되어 있으나 사용되지 않고 있습니다.
- **영향**: DB 유출 시 모든 사용자/관리자 비밀번호가 평문으로 노출
- **AS-IS**:
  ```python
  # workspace/app/routers/user.py:81-83
  user = UserAccount(
      user_email=payload.user_email,
      password_hash=payload.password_hash,  # 해시되지 않은 값이 그대로 저장됨
      ...
  )
  ```
- **TO-BE**:
  ```python
  # workspace/app/routers/user.py:81-83
  from app.core.security import get_password_hash

  user = UserAccount(
      user_email=payload.user_email,
      password_hash=get_password_hash(payload.password_hash),  # bcrypt 해싱 후 저장
      ...
  )
  ```
  > 동일한 수정을 [`workspace/app/routers/admin.py:81-83`](../workspace/app/routers/admin.py:81-83)에도 적용해야 합니다.

---

### C-3. 관리자 인증이 해시 비교가 아닌 DB 값 직접 비교 (보안)

- **파일**: [`workspace/app/crud/admin_crud.py:118-128`](../workspace/app/crud/admin_crud.py:118-128)
- **문제**: `AdminAccountCRUD.authenticate()` 메서드가 `password_hash` 필드를 SQL WHERE 절에서 직접 비교합니다. 이는 bcrypt 해시의 특성(매번 다른 salt 생성)을 무시하며, [`workspace/app/core/security.py:13`](../workspace/app/core/security.py:13)에 구현된 `verify_password()` 함수를 사용하지 않습니다.
- **영향**: 인증이 항상 실패하거나(해시가 다르므로), 평문 비교 시 보안이 완전히 무력화됨
- **AS-IS**:
  ```python
  # workspace/app/crud/admin_crud.py:118-128
  def authenticate(self, db: Session, email: str, password_hash: str) -> Optional[AdminAccount]:
      stmt = (
          select(AdminAccount)
          .where(AdminAccount.admin_email == email)
          .where(AdminAccount.password_hash == password_hash)  # SQL 직접 비교
          .where(AdminAccount.deleted_at.is_(None))
      )
      return db.scalar(stmt)
  ```
- **TO-BE**:
  ```python
  # workspace/app/crud/admin_crud.py:118-128
  from app.core.security import verify_password

  def authenticate(self, db: Session, email: str, plain_password: str) -> Optional[AdminAccount]:
      stmt = (
          select(AdminAccount)
          .where(AdminAccount.admin_email == email)
          .where(AdminAccount.deleted_at.is_(None))
      )
      admin = db.scalar(stmt)
      if admin and verify_password(plain_password, admin.password_hash):
          return admin
      return None
  ```

---

### C-4. 인증/인가 미들웨어 누적 누락 (보안)

- **파일**: 모든 라우터 파일 (`workspace/app/routers/*.py`)
- **문제**: [`workspace/app/dependencies.py:21`](../workspace/app/dependencies.py:21)에 `get_current_user()` 의존성이 구현되어 있으나, **어느 라우터에서도 사용되지 않고 있습니다**. 모든 엔드포인트가 인증 없이 접근 가능합니다. 특히 관리자 API(`/admin/*`), 결제 API(`/payments/*`), 회원 개인정보 API(`/users/*`)는 반드시 인증이 필요합니다.
- **영향**: 모든 API가 인증 없이 호출 가능 → 데이터 유출 및 무단 조작
- **AS-IS**:
  ```python
  # workspace/app/routers/user.py:67
  def get_user(user_id: int, db: Session = Depends(get_db)) -> ...:
  ```
- **TO-BE**:
  ```python
  # workspace/app/routers/user.py:67
  from app.dependencies import get_current_user

  def get_user(
      user_id: int,
      db: Session = Depends(get_db),
      current_user: dict = Depends(get_current_user),
  ) -> ...:
  ```
  > 모든 라우터의 민감 엔드포인트에 동일 패턴 적용 필요

---

### C-5. 민감 정보가 API 응답에 포함됨 (보안)

- **파일**: [`workspace/app/schemas/user.py:44-55`](../workspace/app/schemas/user.py:44-55), [`workspace/app/schemas/admin.py:94-104`](../workspace/app/schemas/admin.py:94-104), [`workspace/app/schemas/payment.py:32-34`](../workspace/app/schemas/payment.py:32-34)
- **문제**: `UserAuthRead` 스키마에 `refresh_token` 필드가, `AdminAccountRead`에 `password_hash` 필드가, `PaymentMethodRead`에 `card_token`/`card_last4` 필드가 응답 스키마에 포함되어 있습니다. 이 값들은 API 응답 시 항상 클라이언트에 노출됩니다.
- **영향**: 토큰/카드 정보 노출 → 계정 탈취 및 결제 정보 유출
- **AS-IS**:
  ```python
  # workspace/app/schemas/user.py:50-51
  class UserAuthRead(TimestampSchema):
      ...
      refresh_token: Optional[str] = None  # 응답에 포함됨
  ```
- **TO-BE**:
  ```python
  # workspace/app/schemas/user.py:50-51
  class UserAuthRead(TimestampSchema):
      ...
      # refresh_token 필드 제거 (별도 내부 전용 스키마로 분리)
  ```
  > 동일하게 `AdminAccountRead`에서 `password_hash` 제거, `PaymentMethodRead`에서 `card_token`/`card_last4` 제거

---

## 🟡 Warning (권장 개선)

### W-1. 동기(Sync) SQLAlchemy 세션 — 비동기 미사용 (성능)

- **파일**: [`workspace/app/database.py:26-38`](../workspace/app/database.py:26-38)
- **문제**: FastAPI는 비동기 프레임워크이지만, `create_engine`(동기)과 `Session`(동기)을 사용하고 있습니다. 모든 라우터 함수가 `def`(동기)로 선언되어 있습니다. [`workspace/app/core/exceptions.py:21`](../workspace/app/core/exceptions.py:21)의 예외 핸들러만 `async def`로 선언되어 일관성이 없습니다.
- **영향**: 동기 호출이 이벤트 루프를 블로킹하여 동시 요청 처리 성능 저하
- **AS-IS**:
  ```python
  # workspace/app/database.py:26-30
  engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, ...)
  SessionLocal = sessionmaker(bind=engine, class_=Session)
  ```
- **TO-BE**:
  ```python
  # workspace/app/database.py
  from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

  engine = create_async_engine(settings.SQLALCHEMY_ASYNC_DATABASE_URI, ...)
  SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession)
  ```
  > 단, 이 변경은 전면적인 async/await 리팩토링이 필요하므로 단계적 적용 권장

---

### W-2. 라우터 전체의 CRUD 중복 패턴 (품질/DRY)

- **파일**: 모든 라우터 파일 (`workspace/app/routers/*.py`)
- **문제**: 모든 라우터가 동일한 CRUD 패턴을 반복하고 있습니다.
  - `_query()` 헬퍼 함수 (selectinload + soft delete 필터)
  - `_get_or_404()` 헬퍼 함수
  - `list_*`, `get_*`, `create_*`, `update_*`, `delete_*` 5종 엔드포인트
  - `updated_at` / `deleted_at` 수동 갱신 로직 (`datetime.now(timezone.utc).replace(tzinfo=None)` 패턴이 20회 이상 반복)
- **영향**: 유지보수성 저하, 버그 발생 시 모든 라우터를 개별 수정해야 함
- **AS-IS** (20개 이상의 라우터에서 반복):
  ```python
  # workspace/app/routers/user.py:111-112
  if update_data:
      user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
  ```
- **TO-BE**:
  ```python
  # 공통 유틸리티 함수로 추출
  from app.utils import touch_updated_at, soft_delete

  # 라우터에서는:
  touch_updated_at(user, update_data)
  # 또는
  soft_delete(user)
  ```

---

### W-3. `datetime.now(timezone.utc).replace(tzinfo=None)` 패턴 반복 (품질)

- **파일**: 20개 이상의 위치 (모든 라우터의 update/delete 엔드포인트)
- **문제**: UTC 시간을 얻은 후 `tzinfo=None`으로 타임존 정보를 제거하는 패턴이 모든 라우터에서 반복됩니다. 이는 실수로 타임존 정보가 포함된 datetime과 비교 시 문제를 일으킬 수 있습니다.
- **영향**: 코드 중복 및 휴먼 에러 가능성
- **AS-IS**:
  ```python
  datetime.now(timezone.utc).replace(tzinfo=None)
  ```
- **TO-BE**:
  ```python
  # 공통 유틸리티
  from datetime import datetime, timezone

  def utcnow() -> datetime:
      """타임존 정보가 없는 UTC 현재 시간을 반환한다."""
      return datetime.now(timezone.utc).replace(tzinfo=None)

  # 사용처
  utcnow()
  ```

---

### W-4. N+1 쿼리 가능성 — selectinload 누락 (성능)

- **파일**: [`workspace/app/routers/admin.py:143`](../workspace/app/routers/admin.py:143), [`workspace/app/routers/search.py:122`](../workspace/app/routers/search.py:122) 등
- **문제**: 일부 목록 조회 엔드포인트에서 `selectinload` 없이 단순 `select(Model)`만 사용하고 있습니다. 예를 들어 `AdminRole` 목록 조회 시 연관된 `permissions`가 로딩되지 않아, 이후 접근 시 N+1 쿼리가 발생합니다.
- **영향**: 목록 조회 시 불필요한 추가 쿼리 발생 → 성능 저하
- **AS-IS**:
  ```python
  # workspace/app/routers/admin.py:143
  statement = select(AdminRole).offset(skip).limit(limit)
  roles = db.execute(statement).scalars().all()
  ```
- **TO-BE**:
  ```python
  # workspace/app/routers/admin.py:143
  statement = (
      select(AdminRole)
      .options(selectinload(AdminRole.permissions))
      .offset(skip).limit(limit)
  )
  roles = db.execute(statement).scalars().all()
  ```

---

### W-5. `password_hash` 필드명 오용 (품질/컨벤션)

- **파일**: [`workspace/app/schemas/user.py:82`](../workspace/app/schemas/user.py:82), [`workspace/app/schemas/admin.py:73`](../workspace/app/schemas/admin.py:73), [`workspace/app/models/user.py:20`](../workspace/app/models/user.py:20), [`workspace/app/models/admin.py:20`](../workspace/app/models/admin.py:20)
- **문제**: 필드명이 `password_hash`이지만, 실제로는 클라이언트가 평문 비밀번호를 보내는 필드로 사용되고 있습니다. 필드명이 해시를 암시하므로 클라이언트가 이미 해시된 값을 보내야 한다고 오해할 수 있습니다.
- **영향**: API 사용성 저하 및 보안 오해 소지
- **AS-IS**:
  ```python
  # workspace/app/schemas/user.py:82
  password_hash: Optional[str] = None
  ```
- **TO-BE**:
  ```python
  # workspace/app/schemas/user.py:82
  password: Optional[str] = Field(default=None, alias="password", description="평문 비밀번호 (서버에서 bcrypt 해싱)")
  ```

---

### W-6. `__init__.py` import 과다 (품질)

- **파일**: [`workspace/app/crud/__init__.py`](../workspace/app/crud/__init__.py) (351줄)
- **문제**: 모든 CRUD 클래스와 인스턴스를 단일 `__init__.py`에 import하고 있습니다. 이는 모듈 로딩 시간 증가와 순환 참조 위험을 초래합니다.
- **영향**: 모듈 import 시간 증가, 순환 참조 디버깅 어려움
- **TO-BE**:
  ```python
  # workspace/app/crud/__init__.py
  # 개별 도메인 import 제거, 필요한 곳에서 직접 import
  # 예: from app.crud.user_crud import user_account_crud
  ```

---

### W-7. `main.py`의 라우터 등록 중복 (품질)

- **파일**: [`workspace/app/main.py:9-18`](../workspace/app/main.py:9-18), [`workspace/app/routers/__init__.py:3-12`](../workspace/app/routers/__init__.py:3-12)
- **문제**: 라우터 import가 `main.py`와 `routers/__init__.py`에서 중복되고 있습니다. `main.py`는 `api_router` 하나만 import하고, `routers/__init__.py`에서 모든 라우터를 집계하는 것이 단일 책임 원칙에 부합합니다.
- **영향**: 새 라우터 추가 시 두 파일을 모두 수정해야 함
- **AS-IS**:
  ```python
  # workspace/app/main.py:9-18
  from app.routers.user import router as user_router
  from app.routers.order import router as order_router
  # ... 8개 더 ...
  ```
- **TO-BE**:
  ```python
  # workspace/app/main.py
  from app.routers import api_router  # 이것만 유지

  application.include_router(api_router, prefix=settings.API_V1_PREFIX)
  ```

---

### W-8. 예외 처리 일관성 부족 (품질)

- **파일**: [`workspace/app/core/exceptions.py:5`](../workspace/app/core/exceptions.py:5), 모든 라우터
- **문제**: [`workspace/app/core/exceptions.py:14`](../workspace/app/core/exceptions.py:14)에 `ResourceNotFoundException`이 정의되어 있으나, 모든 라우터는 `HTTPException`을 직접 raise하고 있습니다. 커스텀 예외 클래스를 활용하면 일관된 에러 응답 형식을 보장할 수 있습니다.
- **영향**: 에러 응답 형식 불일치, 중복 코드
- **AS-IS**:
  ```python
  # workspace/app/routers/user.py:37-40
  raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="회원을 찾을 수 없습니다.",
  )
  ```
- **TO-BE**:
  ```python
  # workspace/app/routers/user.py:37-40
  from app.core.exceptions import ResourceNotFoundException

  raise ResourceNotFoundException("회원을 찾을 수 없습니다.")
  ```

---

### W-9. `__all__` 누락 또는 불완전 (품질/컨벤션)

- **파일**: [`workspace/app/routers/product.py`](../workspace/app/routers/product.py), [`workspace/app/routers/cart.py`](../workspace/app/routers/cart.py), [`workspace/app/routers/inventory.py`](../workspace/app/routers/inventory.py), [`workspace/app/routers/promotion.py`](../workspace/app/routers/promotion.py), [`workspace/app/routers/review.py`](../workspace/app/routers/review.py), [`workspace/app/routers/search.py`](../workspace/app/routers/search.py), [`workspace/app/routers/shipment.py`](../workspace/app/routers/shipment.py)
- **문제**: 일부 라우터 파일에 `__all__`이 누락되었거나, `__all__ = ["router"]`가 있지만 일부는 누락되어 있습니다. 일관된 `__all__` 선언이 필요합니다.
- **영향**: `from module import *` 시 예상치 못한 심볼 노출
- **TO-BE**: 모든 라우터 파일에 `__all__ = ["router"]` 추가

---

### W-10. `card_token` 평문 저장 (보안/규정)

- **파일**: [`workspace/app/models/payment.py:103-104`](../workspace/app/models/payment.py:103-104), [`workspace/app/schemas/payment.py:33-34`](../workspace/app/schemas/payment.py:33-34)
- **문제**: `PaymentMethod` 모델의 `card_token`과 `card_last4`가 평문으로 저장됩니다. PCI-DSS 규정에 따라 카드 토큰은 반드시 암호화되어야 합니다.
- **영향**: PCI-DSS 규정 위반, 법적 책임 발생 가능
- **AS-IS**:
  ```python
  card_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  ```
- **TO-BE**:
  ```python
  # 필드 암호화 (예: SQLAlchemy의 EncryptedType 또는 별도 암호화 레이어)
  from sqlalchemy_utils import EncryptedType

  card_token: Mapped[Optional[str]] = mapped_column(
      EncryptedType(type_in=String(255), key=settings.FIELD_ENCRYPTION_KEY),
      nullable=True,
  )
  ```

---

## 요약 (Summary)

| 구분 | 건수 | 주요 내용 |
|------|------|-----------|
| 🔴 Critical | 5 | 시크릿 키 하드코딩, 비밀번호 해시 누락, 관리자 인증 로직 오류, 인증 미들웨어 미적용, 민감정보 응답 노출 |
| 🟡 Warning | 10 | 동기 DB 세션, CRUD 중복 패턴, datetime 반복, N+1 가능성, 필드명 오용, __init__.py 과다, 라우터 등록 중복, 예외 처리 불일치, __all__ 누락, 카드토큰 평문 저장 |

---

## 치명적 결함 Top 3

1. **🔴 C-1: 하드코딩된 시크릿 키** — [`workspace/app/core/config.py:30`](../workspace/app/core/config.py:30)  
   `SECRET_KEY = "change-me"`가 JWT 서명에 사용됨. 배포 전 반드시 변경 필요.

2. **🔴 C-2: 비밀번호 해시 누락** — [`workspace/app/routers/user.py:81`](../workspace/app/routers/user.py:81), [`workspace/app/routers/admin.py:81`](../workspace/app/routers/admin.py:81)  
   `get_password_hash()`가 구현되어 있으나 사용되지 않고, 평문이 DB에 직접 저장됨.

3. **🔴 C-3: 관리자 인증 로직 오류** — [`workspace/app/crud/admin_crud.py:118`](../workspace/app/crud/admin_crud.py:118)  
   bcrypt 해시를 SQL WHERE 절에서 직접 비교하여 인증이 정상 동작하지 않음.
