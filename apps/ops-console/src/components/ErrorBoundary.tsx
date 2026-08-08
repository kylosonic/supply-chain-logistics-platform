import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="fp-radius-panel border border-red-800/40 bg-slate-900/60 p-8 text-center">
          <div className="mx-auto mb-4 inline-grid h-14 w-14 place-items-center fp-radius-panel bg-red-500/15">
            <svg className="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="mb-2 font-['Space_Grotesk'] text-lg font-semibold text-slate-100">Something went wrong</h2>
          <p className="mb-6 text-sm text-slate-400">
            {this.state.error?.message || 'An unexpected error occurred in this workspace surface.'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="inline-flex min-h-10 items-center rounded-full border border-slate-700 bg-slate-900 px-5 text-sm font-semibold text-slate-200 transition hover:border-slate-500"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

interface PageErrorBoundaryProps {
  children: ReactNode;
  pageName?: string;
}

export function PageErrorBoundary({ children, pageName }: PageErrorBoundaryProps) {
  return (
    <ErrorBoundary
      fallback={
        <div className="fp-radius-panel border border-red-800/40 bg-slate-900/60 p-10 text-center">
          <div className="mx-auto mb-5 inline-grid h-16 w-16 place-items-center fp-radius-panel bg-red-500/15">
            <svg className="h-7 w-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="mb-2 font-['Space_Grotesk'] text-xl font-semibold text-slate-100">
            {pageName ? `${pageName} surface crashed` : 'Surface unavailable'}
          </h2>
          <p className="text-sm text-slate-400">
            The workspace surface encountered an error. Other workspace views remain functional.
          </p>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}
