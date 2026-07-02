import { Component, type ReactNode } from "react";

interface Props {
	children: ReactNode;
}

interface State {
	hasError: boolean;
	error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
	constructor(props: Props) {
		super(props);
		this.state = { hasError: false, error: null };
	}

	static getDerivedStateFromError(error: Error): State {
		console.error("[ErrorBoundary]", error.message, error.stack?.slice(0, 300));
		return { hasError: true, error };
	}

	render() {
		if (this.state.hasError) {
			return (
				<div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-6 text-center">
					<h2 className="text-lg font-semibold text-foreground">
						Something went wrong
					</h2>
					<p className="text-sm text-muted-foreground">
						{this.state.error?.message ?? "An unexpected error occurred."}
					</p>
					<button
						type="button"
						className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/80"
						onClick={() => this.setState({ hasError: false, error: null })}
					>
						Try again
					</button>
				</div>
			);
		}
		return this.props.children;
	}
}
