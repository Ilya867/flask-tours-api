from flask import Flask
from flask_restx import Api, Resource, fields

app = Flask(__name__)
api = Api(app, 
          title='API Туристические поездки',
          description='Веб-сервис для управления турами (Вариант 13)',
          version='1.0',
          doc='/docs/')

# Модель данных для Swagger документации
tour_model = api.model('Tour', {
    'id': fields.Integer(required=True, description='Уникальный идентификатор тура'),
    'country': fields.String(required=True, description='Страна назначения', example='Турция'),
    'hotel_name': fields.String(required=True, description='Название отеля', example='Sunny Beach Hotel'),
    'tour_type': fields.String(required=True, description='Тип тура', example='Пляжный'),
    'price': fields.Float(required=True, description='Стоимость тура в рублях', example=45000.0),
    'duration_days': fields.Integer(required=True, description='Длительность тура в днях', example=7)
})

# Модель для обновления тура (все поля необязательные)
tour_update_model = api.model('TourUpdate', {
    'country': fields.String(description='Страна назначения'),
    'hotel_name': fields.String(description='Название отеля'),
    'tour_type': fields.String(description='Тип тура'),
    'price': fields.Float(description='Стоимость тура в рублях'),
    'duration_days': fields.Integer(description='Длительность тура в днях')
})

# Хранилище данных (в памяти)
tours_db = []
next_id = 1

# Добавляем начальные данные
initial_tours = [
    {"id": None, "country": "Турция", "hotel_name": "Sunny Beach", "tour_type": "Пляжный", "price": 45000, "duration_days": 7},
    {"id": None, "country": "Италия", "hotel_name": "Rome Palace", "tour_type": "Экскурсионный", "price": 85000, "duration_days": 5},
    {"id": None, "country": "Египет", "hotel_name": "Red Sea Resort", "tour_type": "Пляжный", "price": 35000, "duration_days": 10},
    {"id": None, "country": "Франция", "hotel_name": "Paris Charm", "tour_type": "Экскурсионный", "price": 95000, "duration_days": 6},
]

for tour in initial_tours:
    tour["id"] = next_id
    tours_db.append(tour)
    next_id += 1

# Создаём пространство имён для туров
ns_tours = api.namespace('tours', description='Операции с турами')

@ns_tours.route('/')
class ToursList(Resource):
    @ns_tours.doc('get_all_tours')
    @ns_tours.param('sort_by', 'Поле для сортировки (id, country, hotel_name, tour_type, price, duration_days)', 
                    _in='query', required=False)
    @ns_tours.param('order', 'Порядок сортировки (asc или desc)', 
                    _in='query', required=False, default='asc')
    @ns_tours.marshal_list_with(tour_model)
    def get(self):
        """Получить список всех туров с возможностью сортировки"""
        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'asc')
        
        # Проверяем, существует ли поле для сортировки
        valid_fields = ['id', 'country', 'hotel_name', 'tour_type', 'price', 'duration_days']
        if sort_by not in valid_fields:
            sort_by = 'id'
        
        # Сортируем
        sorted_tours = sorted(tours_db, key=lambda x: x.get(sort_by, 0))
        if order == 'desc':
            sorted_tours = list(reversed(sorted_tours))
        
        return sorted_tours
    
    @ns_tours.doc('create_tour')
    @ns_tours.expect(tour_model)
    @ns_tours.marshal_with(tour_model, code=201)
    def post(self):
        """Создать новый тур"""
        global next_id
        data = api.payload
        new_tour = {
            'id': next_id,
            'country': data['country'],
            'hotel_name': data['hotel_name'],
            'tour_type': data['tour_type'],
            'price': data['price'],
            'duration_days': data['duration_days']
        }
        tours_db.append(new_tour)
        next_id += 1
        return new_tour, 201

@ns_tours.route('/<int:tour_id>')
@ns_tours.response(404, 'Тур не найден')
@ns_tours.param('tour_id', 'Идентификатор тура')
class TourResource(Resource):
    @ns_tours.doc('get_tour')
    @ns_tours.marshal_with(tour_model)
    def get(self, tour_id):
        """Получить тур по ID"""
        tour = next((t for t in tours_db if t['id'] == tour_id), None)
        if tour is None:
            api.abort(404, f'Тур с ID {tour_id} не найден')
        return tour
    
    @ns_tours.doc('update_tour')
    @ns_tours.expect(tour_update_model)
    @ns_tours.marshal_with(tour_model)
    def put(self, tour_id):
        """Обновить тур по ID"""
        tour = next((t for t in tours_db if t['id'] == tour_id), None)
        if tour is None:
            api.abort(404, f'Тур с ID {tour_id} не найден')
        
        data = api.payload
        if 'country' in data:
            tour['country'] = data['country']
        if 'hotel_name' in data:
            tour['hotel_name'] = data['hotel_name']
        if 'tour_type' in data:
            tour['tour_type'] = data['tour_type']
        if 'price' in data:
            tour['price'] = data['price']
        if 'duration_days' in data:
            tour['duration_days'] = data['duration_days']
        
        return tour
    
    @ns_tours.doc('delete_tour')
    @ns_tours.response(204, 'Тур удалён')
    def delete(self, tour_id):
        """Удалить тур по ID"""
        global tours_db
        tour = next((t for t in tours_db if t['id'] == tour_id), None)
        if tour is None:
            api.abort(404, f'Тур с ID {tour_id} не найден')
        tours_db = [t for t in tours_db if t['id'] != tour_id]
        return '', 204

@ns_tours.route('/stats/')
class ToursStats(Resource):
    @ns_tours.doc('get_stats')
    def get(self):
        """Получить статистику по числовым полям (min, max, avg)"""
        if not tours_db:
            return {
                'price': {'min': None, 'max': None, 'avg': None},
                'duration_days': {'min': None, 'max': None, 'avg': None}
            }
        
        prices = [t['price'] for t in tours_db]
        durations = [t['duration_days'] for t in tours_db]
        
        return {
            'price': {
                'min': min(prices),
                'max': max(prices),
                'avg': round(sum(prices) / len(prices), 2)
            },
            'duration_days': {
                'min': min(durations),
                'max': max(durations),
                'avg': round(sum(durations) / len(durations), 2)
            }
        }

# Регистрируем пространство имён
api.add_namespace(ns_tours)

# Добавляем импорт request
from flask import request

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
