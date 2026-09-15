# Seguimiento en tiempo real (SocketIO)

Esta funcionalidad permite ver en el mapa la ubicacion de funcionarios en tiempo real usando SocketIO. El backend simula el movimiento sumando pequenos desplazamientos a la latitud y longitud y emite un evento periodico.

## Requisitos para que un funcionario sea rastreado

- `gps_active` en `true`
- `status` en `active` o `activo`
- `last_latitude` y `last_longitude` con valores no nulos

## Endpoints

### Iniciar seguimiento de funcionarios

```text
POST /api/officials/tracking/start
```

```json
{ "ids": [1, 2, 3] }
```

### Detener seguimiento de todos

```text
POST /api/officials/tracking/stop
```

```json
{}
```

### Detener seguimiento de algunos

```text
POST /api/officials/tracking/stop
```

```json
{ "ids": [1, 2] }
```

## Evento SocketIO

```text
event: official_tracking
payload: { "officials": [ { "id_official": 1, "latitude": 6.24, "longitude": -75.58, "last_gps_update": "2026-05-27T14:00:00" } ] }
```
