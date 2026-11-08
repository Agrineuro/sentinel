import { Handle, Position, type NodeProps } from '@xyflow/react'
import {
  Bell,
  BrainCircuit,
  Camera,
  Database,
  Eye,
  House,
  Mic2,
  Radio,
  ShieldCheck,
  Workflow,
} from 'lucide-react'
import type { HealthState } from '../types'

type NodeData = {
  label: string
  subtitle: string
  status: HealthState
  icon: string
  kind?: 'hub' | 'standard' | 'leaf'
}

const icons = {
  home: House,
  shield: ShieldCheck,
  camera: Camera,
  radio: Radio,
  workflow: Workflow,
  eye: Eye,
  database: Database,
  mic: Mic2,
  bell: Bell,
  brain: BrainCircuit,
}

export function SentinelNode({ data, selected }: NodeProps) {
  const nodeData = data as NodeData
  const Icon = icons[nodeData.icon as keyof typeof icons] ?? ShieldCheck

  return (
    <div className={`sentinel-node ${nodeData.kind ?? 'standard'} status-${nodeData.status} ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} className="node-handle" />
      <Handle type="target" position={Position.Top} className="node-handle" />
      <div className="node-icon"><Icon size={nodeData.kind === 'hub' ? 25 : 20} /></div>
      <div className="node-copy">
        <strong>{nodeData.label}</strong>
        <span>{nodeData.subtitle}</span>
      </div>
      <span className={`node-dot ${nodeData.status}`} />
      <Handle type="source" position={Position.Right} className="node-handle" />
      <Handle type="source" position={Position.Bottom} className="node-handle" />
    </div>
  )
}
