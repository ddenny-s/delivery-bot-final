"""
База данных для хранения доставок
"""
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()


class Delivery(Base):
    """Модель доставки"""
    __tablename__ = 'deliveries'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(100), unique=True, nullable=False)
    service = Column(String(50), nullable=False)
    status = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    pickup_code = Column(String(50), nullable=True)
    recipient_name = Column(String(100), nullable=True)
    estimated_delivery = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def add_delivery(self, delivery_data: dict) -> bool:
        """Добавить доставку"""
        session = self.Session()
        try:
            existing = session.query(Delivery).filter_by(
                order_number=delivery_data['order_number']
            ).first()
            
            if existing:
                existing.status = delivery_data.get('status', existing.status)
                existing.address = delivery_data.get('address', existing.address)
                existing.pickup_code = delivery_data.get('pickup_code', existing.pickup_code)
                existing.estimated_delivery = delivery_data.get('estimated_delivery', existing.estimated_delivery)
                existing.updated_at = datetime.now()
                session.commit()
                return True
            
            delivery = Delivery(
                order_number=delivery_data['order_number'],
                service=delivery_data.get('service', 'Неизвестно'),
                status=delivery_data.get('status', 'Неизвестно'),
                address=delivery_data.get('address'),
                pickup_code=delivery_data.get('pickup_code'),
                recipient_name=delivery_data.get('recipient_name'),
                estimated_delivery=delivery_data.get('estimated_delivery')
            )
            session.add(delivery)
            session.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении доставки: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_active_deliveries(self) -> list:
        """Получить активные доставки"""
        session = self.Session()
        try:
            return session.query(Delivery).filter_by(is_active=True).all()
        finally:
            session.close()
    
    def mark_as_inactive(self, order_number: str) -> bool:
        """Отметить как неактивную"""
        session = self.Session()
        try:
            delivery = session.query(Delivery).filter_by(order_number=order_number).first()
            if delivery:
                delivery.is_active = False
                delivery.updated_at = datetime.now()
                session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def delete_delivery(self, order_number: str) -> bool:
        """Удалить доставку"""
        session = self.Session()
        try:
            delivery = session.query(Delivery).filter_by(order_number=order_number).first()
            if delivery:
                session.delete(delivery)
                session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_statistics(self) -> dict:
        """Получить статистику"""
        session = self.Session()
        try:
            total = session.query(Delivery).count()
            active = session.query(Delivery).filter_by(is_active=True).count()
            
            services = {}
            for delivery in session.query(Delivery).all():
                if delivery.service not in services:
                    services[delivery.service] = 0
                services[delivery.service] += 1
            
            return {
                'всего': total,
                'активных': active,
                'завершенных': total - active,
                'по_сервисам': services
            }
        finally:
            session.close()
