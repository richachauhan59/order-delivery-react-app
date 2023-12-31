from fastapi import FastAPI, Request
from redis_om import get_redis_connection, HashModel
from fastapi.middleware.cors import CORSMiddleware
import json
import consumers

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_methods=['*'],
    allow_headers=['*']
)

redis = get_redis_connection(
    host="redis-16381.c264.ap-south-1-1.ec2.cloud.redislabs.com",
    port=16381,
    password="wKFWN4BR17JwABtM3oTEGwjTwX4S8lQa",
    decode_responses=True
)

class Delivery(HashModel):
    budget: int = 0
    notes: str = ''

    class Meta:
        database = redis


class Event(HashModel):
    delivery_id: str = None
    type: str
    data: str

    class Meta:
        database = redis

@app.get('/deliveries/{pk}/status')
async def get_state(pk: str):
    state = redis.get(f'delivery:{pk}')
    if state is not None:
        return json.loads(state)

    state = build_state(pk)
    return state

def build_state(pk: str):
    pks = Event.all_pk()
    all_events = [Event.get(pk) for pk in pks]
    events = [event for event in all_events if event.delivery_id == pk]
    return events

@app.post('/deliveries/create')
async def create(request: Request):
    body = await request.json()
    delivery = Delivery(budget = body['data']['budget'], notes = body['data']['notes']).save()
    event = Event(delivery_id=delivery.pk, type=body['type'], data=json.dumps(body['data'])).save()
    state = consumers.CONSUMERS[event.type]({}, event)
    redis.set(f'delivery:{delivery.pk}', json.dumps(state))
    return state

@app.post('/event')
async def dispatch(request: Request):
    body = await request.json()
    delivery_id = body['delivery_id']
    event = Event(delivery_id = delivery_id, type = body['type'], data = json.dumps(body['data'])).save()
    state = await get_state(delivery_id)
    new_state = consumers.CONSUMERS[event.type](state, event)
    redis.set(f'delivery:{delivery_id}', json.dumps(new_state))
    return new_state