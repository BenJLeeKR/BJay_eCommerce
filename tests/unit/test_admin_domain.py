from app.models.admin import AdminAccount, AdminRole, AdminPermission
from app.routers.admin import router
from app.schemas.admin import AdminAccountCreate, AdminAccountUpdate


def test_admin_account_table_and_indexes_are_defined() -> None:
    """관리자 계정 모델의 핵심 테이블 메타데이터가 정의되어야 한다."""
    index_names = {index.name for index in AdminAccount.__table__.indexes}

    assert AdminAccount.__tablename__ == "admin_account"
    assert AdminAccount.__table__.c.admin_email.unique is True
    assert AdminAccount.__table__.c.admin_email.nullable is False
    assert AdminAccount.__table__.c.password_hash.nullable is False
    assert AdminAccount.__table__.c.admin_status.nullable is False


def test_admin_role_table_and_indexes_are_defined() -> None:
    """관리자 역할 모델의 핵심 제약 조건이 정의되어야 한다."""
    assert AdminRole.__tablename__ == "admin_role"
    assert AdminRole.__table__.c.role_name.nullable is False


def test_admin_permission_table_and_indexes_are_defined() -> None:
    """권한 모델의 핵심 제약 조건이 정의되어야 한다."""
    assert AdminPermission.__tablename__ == "admin_permission"
    assert AdminPermission.__table__.c.permission_code.unique is True
    assert AdminPermission.__table__.c.permission_code.nullable is False


def test_admin_account_create_schema_validates_required_fields() -> None:
    """관리자 계정 생성 스키마가 핵심 필드를 검증해야 한다."""
    payload = AdminAccountCreate(
        admin_email="admin@example.com",
        password_hash="hashed_password",
        admin_status="ACTIVE",
        last_login_at=None,
        created_by=1,
    )

    assert payload.admin_email == "admin@example.com"
    assert payload.password_hash == "hashed_password"
    assert payload.admin_status == "ACTIVE"
    assert payload.created_by == 1


def test_admin_account_update_schema_supports_partial_update() -> None:
    """관리자 계정 수정 스키마는 부분 업데이트를 지원해야 한다."""
    payload = AdminAccountUpdate(admin_status="INACTIVE", updated_by=2)

    assert payload.model_dump(exclude_unset=True) == {
        "admin_status": "INACTIVE",
        "updated_by": 2,
    }


def test_admin_router_registers_expected_routes() -> None:
    """관리자 라우터에 CRUD 엔드포인트가 등록되어야 한다."""
    route_map = {(tuple(sorted(route.methods)), route.path) for route in router.routes}

    assert (("GET",), "/admin/accounts") in route_map
    assert (("GET",), "/admin/accounts/{admin_id}") in route_map
    assert (("POST",), "/admin/accounts") in route_map
    assert (("PUT",), "/admin/accounts/{admin_id}") in route_map
    assert (("DELETE",), "/admin/accounts/{admin_id}") in route_map
    assert (("GET",), "/admin/roles") in route_map
    assert (("GET",), "/admin/permissions") in route_map