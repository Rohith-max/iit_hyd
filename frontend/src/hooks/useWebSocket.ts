import { useEffect, useRef, useCallback } from 'react';
import { useAgentStore } from '../store';
import type { AgentEvent } from '../types';

export function useWebSocket(caseId: string | undefined) {
  const wsRef = useRef<WebSocket | null>(null);
  const { addEvent, appendCAM, setCurrentAgent, setComplete, reset } = useAgentStore();

  const connect = useCallback(() => {
    if (!caseId) return;
    reset();

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/cases/${caseId}`);
    wsRef.current = ws;

    ws.onmessage = (evt) => {
      try {
        const event: AgentEvent = JSON.parse(evt.data);
        addEvent(event);

        if (event.type === 'agent_start' && event.agent) {
          setCurrentAgent(event.agent);
        }
        if (event.type === 'cam_stream' && event.section && event.delta) {
          appendCAM(event.section, event.delta);
        }
        if (event.type === 'pipeline_complete') {
          setComplete(true);
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };
  }, [caseId, addEvent, appendCAM, setCurrentAgent, setComplete, reset]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { ws: wsRef.current };
}
