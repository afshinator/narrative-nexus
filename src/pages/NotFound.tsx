import { Link } from "react-router";

export default function NotFoundPage() {
	return (
		<div className="mx-auto max-w-[780px] py-16 text-center">
			<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
				Page not found
			</h1>
			<p className="mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				The page you&rsquo;re looking for doesn&rsquo;t exist.
			</p>
			<Link
				to="/"
				className="mt-4 inline-block font-mono text-[0.84rem] text-[var(--nn-navy)] hover:underline"
			>
				&larr; Back to Sources
			</Link>
		</div>
	);
}
