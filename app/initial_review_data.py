#!/usr/bin/env python3

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.compliance_rule import ComplianceRule
from app.models.review_point import ReviewPoint
from app.models.review_stage import ReviewStage
from app.models.role import Role

"""
初始化审查系统数据

创建默认的审查阶段、审查要点和合规规则
"""


def create_default_roles(db: Session):
    """创建默认角色"""
    roles_data = [
        {
            "name": "super_admin",
            "display_name": "超级管理员",
            "description": "系统超级管理员，拥有所有权限",
            "permissions": '{"all": true}',
            "is_active": True,
            "is_system": True,
        },
        {
            "name": "reviewer",
            "display_name": "审查员",
            "description": "项目审查员，负责项目审查工作",
            "permissions": '{"review": true, "document": true}',
            "is_active": True,
        },
        {
            "name": "project_manager",
            "display_name": "项目经理",
            "description": "项目经理，负责项目管理",
            "permissions": '{"project": true, "document": true}',
            "is_active": True,
        },
        {
            "name": "user",
            "display_name": "普通用户",
            "description": "普通用户，基本查看权限",
            "permissions": '{"view": true}',
            "is_active": True,
        },
    ]

    for role_data in roles_data:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(**role_data)
            db.add(role)

    db.commit()
    print("默认角色创建完成")


def create_default_review_stages(db: Session):
    """创建默认审查阶段"""
    stages_data = [
        {
            "name": "立项审查",
            "description": "项目立项阶段的审查，包括项目可行性、必要性等",
            "order_index": 1,
        },
        {
            "name": "采购需求审查",
            "description": "采购需求的合理性、完整性审查",
            "order_index": 2,
        },
        {
            "name": "采购方式审查",
            "description": "采购方式选择的合规性审查",
            "order_index": 3,
        },
        {
            "name": "招标文件审查",
            "description": "招标文件的完整性、合规性审查",
            "order_index": 4,
        },
        {
            "name": "评标结果审查",
            "description": "评标过程和结果的合规性审查",
            "order_index": 5,
        },
        {
            "name": "合同签订审查",
            "description": "合同条款的合规性审查",
            "order_index": 6,
        },
        {
            "name": "履约验收审查",
            "description": "项目履约和验收的审查",
            "order_index": 7,
        },
    ]

    for stage_data in stages_data:
        existing_stage = (
            db.query(ReviewStage).filter(ReviewStage.name == stage_data["name"]).first()
        )
        if not existing_stage:
            stage = ReviewStage(**stage_data)
            db.add(stage)

    db.commit()
    print("默认审查阶段创建完成")


def create_default_review_points(db: Session):
    """创建默认审查要点"""
    # 获取审查阶段
    stages = db.query(ReviewStage).all()
    stage_dict = {stage.name: stage.id for stage in stages}

    points_data = [
        # 立项审查要点
        {
            "stage_id": stage_dict.get("立项审查"),
            "code": "necessity_check",
            "title": "项目必要性审查",
            "description": "审查项目的必要性和紧迫性",
            "review_criteria": "项目是否符合单位职能和发展规划",
            "review_type": "manual",
            "order_index": 1,
        },
        {
            "stage_id": stage_dict.get("立项审查"),
            "code": "budget_reasonableness",
            "title": "预算合理性审查",
            "description": "审查项目预算的合理性和准确性",
            "review_criteria": "预算编制是否科学合理，资金来源是否明确",
            "review_type": "manual",
            "order_index": 2,
        },
        # 采购需求审查要点
        {
            "stage_id": stage_dict.get("采购需求审查"),
            "code": "requirement_completeness",
            "title": "需求完整性审查",
            "description": "审查采购需求的完整性和明确性",
            "review_criteria": "技术规格、数量、质量要求等是否明确完整",
            "review_type": "manual",
            "order_index": 1,
        },
        {
            "stage_id": stage_dict.get("采购需求审查"),
            "code": "technical_standard",
            "title": "技术标准审查",
            "description": "审查技术标准的合规性",
            "review_criteria": "技术标准是否符合国家和行业标准",
            "review_type": "manual",
            "order_index": 2,
        },
        # 采购方式审查要点
        {
            "stage_id": stage_dict.get("采购方式审查"),
            "code": "method_compliance",
            "title": "采购方式合规性",
            "description": "审查采购方式选择的合规性",
            "review_criteria": "采购方式是否符合法律法规要求",
            "review_type": "manual",
            "order_index": 1,
        },
        # 招标文件审查要点
        {
            "stage_id": stage_dict.get("招标文件审查"),
            "code": "document_completeness",
            "title": "招标文件完整性",
            "description": "审查招标文件的完整性",
            "review_criteria": "招标文件是否包含所有必要内容",
            "review_type": "manual",
            "order_index": 1,
        },
        {
            "stage_id": stage_dict.get("招标文件审查"),
            "code": "evaluation_criteria",
            "title": "评标标准合理性",
            "description": "审查评标标准的合理性",
            "review_criteria": "评标标准是否科学合理、公平公正",
            "review_type": "manual",
            "order_index": 2,
        },
    ]

    for point_data in points_data:
        if point_data["stage_id"]:
            existing_point = (
                db.query(ReviewPoint)
                .filter(ReviewPoint.code == point_data["code"])
                .first()
            )
            if not existing_point:
                point = ReviewPoint(**point_data)
                db.add(point)

    db.commit()
    print("默认审查要点创建完成")


def create_default_compliance_rules(db: Session):
    """创建默认合规规则"""
    rules_data = [
        {
            "rule_code": "BUDGET_LIMIT_CHECK",
            "rule_name": "预算限额检查",
            "description": "检查项目预算是否超过规定限额",
            "category": "预算管理",
            "subcategory": "限额控制",
            "applicable_stage": "project_initiation",
            "rule_content": "单个项目预算不得超过年度预算的30%",
            "check_pattern": "budget <= annual_budget * 0.3",
            "severity": "high",
            "legal_basis": "政府采购法实施条例",
            "is_active": True,
            "is_automated": True,
            "version": "1.0",
            "effective_date": datetime.now(),
        },
        {
            "rule_code": "PROCUREMENT_METHOD_CHECK",
            "rule_name": "采购方式合规检查",
            "description": "检查采购方式选择是否符合法规要求",
            "category": "采购程序",
            "subcategory": "方式选择",
            "applicable_stage": "procurement_method",
            "rule_content": "达到公开招标限额标准的必须采用公开招标",
            "check_pattern": "if budget >= public_tender_threshold then method = 'public_tender'",
            "severity": "critical",
            "legal_basis": "政府采购法第二十六条",
            "is_active": True,
            "is_automated": True,
            "version": "1.0",
            "effective_date": datetime.now(),
        },
        {
            "rule_code": "DOCUMENT_COMPLETENESS_CHECK",
            "rule_name": "文档完整性检查",
            "description": "检查招标文件是否包含必要内容",
            "category": "文档管理",
            "subcategory": "完整性",
            "applicable_stage": "tender_document",
            "rule_content": "招标文件必须包含技术规格、商务条款、评标标准等",
            "check_pattern": "required_sections in document_content",
            "severity": "high",
            "legal_basis": "政府采购货物和服务招标投标管理办法",
            "is_active": True,
            "is_automated": False,
            "version": "1.0",
            "effective_date": datetime.now(),
        },
        {
            "rule_code": "EVALUATION_FAIRNESS_CHECK",
            "rule_name": "评标公正性检查",
            "description": "检查评标过程是否公正透明",
            "category": "评标管理",
            "subcategory": "公正性",
            "applicable_stage": "evaluation_result",
            "rule_content": "评标委员会组成应符合规定，评标过程应有完整记录",
            "check_pattern": "evaluation_committee_valid and evaluation_records_complete",
            "severity": "critical",
            "legal_basis": "政府采购法第三十七条",
            "is_active": True,
            "is_automated": False,
            "version": "1.0",
            "effective_date": datetime.now(),
        },
        {
            "rule_code": "CONTRACT_TERMS_CHECK",
            "rule_name": "合同条款检查",
            "description": "检查合同条款是否完整合规",
            "category": "合同管理",
            "subcategory": "条款审查",
            "applicable_stage": "contract_signing",
            "rule_content": "合同应包含标的、数量、质量、价款、履行期限等主要条款",
            "check_pattern": "contract_essential_terms_complete",
            "severity": "high",
            "legal_basis": "合同法",
            "is_active": True,
            "is_automated": False,
            "version": "1.0",
            "effective_date": datetime.now(),
        },
    ]

    for rule_data in rules_data:
        existing_rule = (
            db.query(ComplianceRule)
            .filter(ComplianceRule.rule_code == rule_data["rule_code"])
            .first()
        )
        if not existing_rule:
            rule = ComplianceRule(**rule_data)
            db.add(rule)

    db.commit()
    print("默认合规规则创建完成")


def init_review_data():
    """初始化审查系统数据"""
    db = SessionLocal()
    try:
        print("开始初始化审查系统数据...")

        # 创建默认角色
        create_default_roles(db)

        # 创建默认审查阶段
        create_default_review_stages(db)

        # 创建默认审查要点
        create_default_review_points(db)

        # 创建默认合规规则
        create_default_compliance_rules(db)

        print("审查系统数据初始化完成！")

    except Exception as e:
        print(f"初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_review_data()
