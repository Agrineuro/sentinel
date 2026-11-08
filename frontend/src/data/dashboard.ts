import {
  Activity,
  AlertTriangle,
  Boxes,
  Database,
  DoorOpen,
  Radio,
  ShieldAlert,
  Thermometer,
  UserRound,
} from 'lucide-react'
import type { Connector, Metric, Observation } from '../types'

export const metrics: Metric[] = [
  {
    label: 'Connectors',
    value: '8',
    detail: '1 degraded',
    tone: 'amber',
    icon: Radio,
  },
  {
    label: 'Entities',
    value: '47',
    detail: '2 offline',
    tone: 'red',
    icon: Boxes,
  },
  {
    label: 'Observations today',
    value: '1,249',
    detail: '14 / minute',
    tone: 'blue',
    icon: Activity,
  },
  {
    label: 'Alerts',
    value: '2',
    detail: '1 critical',
    tone: 'red',
    icon: ShieldAlert,
  },
]

export const observations: Observation[] = [
  {
    time: '09:42:17',
    title: 'Person detected at front porch',
    source: 'Frigate · Front Camera',
    category: 'Security',
    tone: 'red',
    icon: UserRound,
  },
  {
    time: '09:41:03',
    title: 'Living room temperature changed to 72°F',
    source: 'Home Assistant · climate.living_room',
    category: 'Environment',
    tone: 'blue',
    icon: Thermometer,
  },
  {
    time: '09:39:48',
    title: 'Immich backup completed',
    source: 'Immich · System',
    category: 'System',
    tone: 'green',
    icon: Database,
  },
  {
    time: '09:38:12',
    title: 'Frigate connector latency increased',
    source: 'Sentinel · Connector Health',
    category: 'Warning',
    tone: 'amber',
    icon: AlertTriangle,
  },
  {
    time: '09:37:21',
    title: 'Front door opened',
    source: 'Home Assistant · binary_sensor.front_door',
    category: 'Environment',
    tone: 'blue',
    icon: DoorOpen,
  },
]

export const connectors: Connector[] = [
  { name: 'Home Assistant', status: 'healthy', rate: '184 events/min', lastSeen: '1s ago' },
  { name: 'Frigate', status: 'healthy', rate: '14 events/min', lastSeen: '2s ago' },
  { name: 'MQTT Broker', status: 'degraded', rate: 'Reconnecting', lastSeen: '4m ago' },
  { name: 'Immich', status: 'healthy', rate: '2 events/min', lastSeen: '18m ago' },
  { name: 'Piper TTS', status: 'healthy', rate: '1 event/min', lastSeen: '2s ago' },
]
