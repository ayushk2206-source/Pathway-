import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Subsystem Error Caught by Boundary:', error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '28px',
          margin: '16px auto',
          maxWidth: '850px',
          background: 'rgba(20, 10, 15, 0.85)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '12px',
          color: '#f87171',
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6), inset 0 0 20px rgba(239, 68, 68, 0.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(239, 68, 68, 0.2)', paddingBottom: '12px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '18px', filter: 'drop-shadow(0 0 6px rgba(239,68,68,0.8))' }}>⚠️</span>
              <span style={{ fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#ff6b6b' }}>
                {this.props.fallbackTitle || 'Subsystem Telemetry Anomaly'}
              </span>
            </div>
            <span style={{ fontSize: '11px', color: '#9ca3af', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '4px' }}>
              RECOVERY MATRIX ARMED
            </span>
          </div>

          <p style={{ fontSize: '13px', color: '#d1d5db', lineHeight: 1.6, margin: '0 0 14px 0' }}>
            A temporary component state discrepancy was intercepted before causing an interface unmount. The underlying neural engine remains operational.
          </p>

          {this.state.error && (
            <div style={{
              background: 'rgba(0, 0, 0, 0.6)',
              padding: '12px',
              borderRadius: '6px',
              fontSize: '12px',
              color: '#fca5a5',
              borderLeft: '3px solid #ef4444',
              marginBottom: '16px',
              overflowX: 'auto',
              whiteSpace: 'pre-wrap'
            }}>
              {this.state.error.toString()}
            </div>
          )}

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button
              onClick={this.handleReset}
              style={{
                background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(220, 38, 38, 0.6))',
                border: '1px solid rgba(239, 68, 68, 0.8)',
                color: '#fff',
                padding: '8px 18px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '12px',
                letterSpacing: '0.05em',
                transition: 'all 0.2s ease',
                boxShadow: '0 0 15px rgba(239,68,68,0.3)'
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(239, 68, 68, 0.8)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(220, 38, 38, 0.6))')}
            >
              ↺ RE-ENGAGE SUBSYSTEM
            </button>
            <span style={{ fontSize: '11px', color: '#6b7280' }}>
              Fault isolated to viewport module.
            </span>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
