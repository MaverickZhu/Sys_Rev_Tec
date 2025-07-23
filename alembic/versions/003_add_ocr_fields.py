"""Add OCR fields to document table

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '1e936bea7a27'
branch_labels = None
depends_on = None

def upgrade():
    # Add new OCR-related columns to documents table
    op.add_column('documents', sa.Column('ocr_engine', sa.String(50), nullable=True, comment='使用的OCR引擎'))
    op.add_column('documents', sa.Column('ocr_confidence', sa.Integer(), nullable=True, comment='OCR识别置信度(0-100)'))
    op.add_column('documents', sa.Column('is_handwritten', sa.Boolean(), nullable=True, comment='是否包含手写内容'))
    op.add_column('documents', sa.Column('ocr_details', sa.Text(), nullable=True, comment='OCR详细信息(JSON格式)'))
    
    # Create indexes for better query performance
    op.create_index('ix_documents_ocr_engine', 'documents', ['ocr_engine'])
    op.create_index('ix_documents_is_handwritten', 'documents', ['is_handwritten'])
    op.create_index('ix_documents_ocr_confidence', 'documents', ['ocr_confidence'])

def downgrade():
    # Drop indexes
    op.drop_index('ix_documents_ocr_confidence', table_name='documents')
    op.drop_index('ix_documents_is_handwritten', table_name='documents')
    op.drop_index('ix_documents_ocr_engine', table_name='documents')
    
    # Drop columns
    op.drop_column('documents', 'ocr_details')
    op.drop_column('documents', 'is_handwritten')
    op.drop_column('documents', 'ocr_confidence')
    op.drop_column('documents', 'ocr_engine')