from datetime import datetime
import uuid
from extensions import db

class PolicyDocument(db.Model):
    __tablename__ = "policy_documents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    file_hash = db.Column(db.String(64), nullable=True)
    chunks_count = db.Column(db.Integer, default=0)
    uploaded_by = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "filename": self.filename,
            "file_size": self.file_size,
            "chunks_count": self.chunks_count,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
