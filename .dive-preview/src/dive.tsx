import { useSQLQuery } from '@motherduck/react-sql-query';
import {
	Area,
	AreaChart,
	Bar,
	BarChart,
	CartesianGrid,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from 'recharts';

export const REQUIRED_DATABASES = [
	{
		type: 'database',
		path: 'md:marketstack_test',
		alias: 'marketstack_test',
	},
];

const PRIMARY = '#0777b3';
const POSITIVE = '#2d7a00';
const NEGATIVE = '#bc1200';
const MUTED = '#6a6a6a';
const TEXT = '#231f20';

const N = (v: unknown): number => (v == null ? 0 : Number(v));

const fmtUsd = (v: number) => `$${v.toFixed(2)}`;
const fmtPct = (v: number) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
const fmtVol = (v: number) => `${(v / 1e6).toFixed(1)}M`;
const fmtDateShort = (s: string) =>
	new Date(`${s}T00:00:00Z`).toLocaleDateString('en-US', {
		month: 'short',
		day: 'numeric',
		timeZone: 'UTC',
	});

function KpiSkeleton() {
	return <div className="h-10 w-24 animate-pulse rounded bg-gray-200" />;
}

function ChartSkeleton({ height }: { height: number }) {
	return (
		<div
			className="animate-pulse rounded bg-gray-100"
			style={{ height }}
		/>
	);
}

export default function AaplSnapshotDive() {
	const rowsQuery = useSQLQuery(`
    SELECT trade_date, close, prior_close, daily_return_pct, volume
    FROM "marketstack_test"."gold"."aapl_daily_returns"
    WHERE close IS NOT NULL
    ORDER BY trade_date
  `);

	const raw = Array.isArray(rowsQuery.data) ? rowsQuery.data : [];
	const rows = raw.map((r) => ({
		date: String(r.trade_date),
		close: N(r.close),
		return_pct: r.daily_return_pct == null ? null : N(r.daily_return_pct),
		volume: N(r.volume),
	}));

	const hasRows = rows.length > 0;
	const first = hasRows ? rows[0] : null;
	const last = hasRows ? rows[rows.length - 1] : null;
	const closes = rows.map((r) => r.close);
	const minClose = hasRows ? Math.min(...closes) : 0;
	const maxClose = hasRows ? Math.max(...closes) : 0;
	const avgVolume = hasRows
		? rows.reduce((s, r) => s + r.volume, 0) / rows.length
		: 0;
	const totalChangePct =
		first && last && first.close !== 0
			? ((last.close - first.close) / first.close) * 100
			: 0;

	const returns = rows.filter(
		(r): r is typeof r & { return_pct: number } => r.return_pct != null,
	);
	const bestDay = returns.length
		? returns.reduce((a, b) => (b.return_pct > a.return_pct ? b : a))
		: null;
	const worstDay = returns.length
		? returns.reduce((a, b) => (b.return_pct < a.return_pct ? b : a))
		: null;
	const peakVolumeDay = hasRows
		? rows.reduce((a, b) => (b.volume > a.volume ? b : a))
		: null;

	const priceChartData = rows.map((r) => ({
		date: fmtDateShort(r.date),
		close: r.close,
	}));
	const volumeChartData = rows.map((r) => ({
		date: fmtDateShort(r.date),
		volume: r.volume,
	}));

	const loading = rowsQuery.isLoading;
	const errored = rowsQuery.isError;

	return (
		<main className="p-6" style={{ background: '#f8f8f8' }}>
			<div className="mb-6 flex items-end justify-between gap-4">
				<div>
					<div
						className="mb-1 inline-block rounded px-2 py-0.5 text-xs font-medium"
						style={{ background: '#e6f0f7', color: PRIMARY }}
					>
						NASDAQ · AAPL
					</div>
					<h1
						className="text-2xl font-semibold"
						style={{ color: TEXT }}
					>
						Apple Inc. — End-of-Day Snapshot
					</h1>
					<p className="text-sm" style={{ color: MUTED }}>
						Daily closes and volume from marketstack EOD, gold
						layer
					</p>
				</div>
			</div>

			{errored ? (
				<p className="text-sm" style={{ color: NEGATIVE }} role="alert">
					{String(rowsQuery.error)}
				</p>
			) : (
				<>
					{/* KPI row */}
					<div className="mb-8 grid grid-cols-4 gap-8">
						<div>
							{loading ? (
								<KpiSkeleton />
							) : (
								<p
									className="text-3xl font-bold"
									style={{ color: TEXT }}
								>
									{first && last
										? `${fmtDateShort(first.date)} – ${fmtDateShort(last.date)}`
										: '—'}
								</p>
							)}
							<p className="mt-1 text-sm" style={{ color: MUTED }}>
								Period
							</p>
						</div>
						<div>
							{loading ? (
								<KpiSkeleton />
							) : (
								<p
									className="text-3xl font-bold"
									style={{ color: TEXT }}
								>
									{last ? fmtUsd(last.close) : '—'}
								</p>
							)}
							<p
								className="mt-1 text-sm"
								style={{
									color: totalChangePct >= 0 ? POSITIVE : NEGATIVE,
								}}
							>
								{hasRows ? `${fmtPct(totalChangePct)} over period` : ' '}
							</p>
						</div>
						<div>
							{loading ? (
								<KpiSkeleton />
							) : (
								<p
									className="text-3xl font-bold"
									style={{ color: TEXT }}
								>
									{hasRows
										? `${fmtUsd(minClose)} – ${fmtUsd(maxClose)}`
										: '—'}
								</p>
							)}
							<p className="mt-1 text-sm" style={{ color: MUTED }}>
								Close range, period
							</p>
						</div>
						<div>
							{loading ? (
								<KpiSkeleton />
							) : (
								<p
									className="text-3xl font-bold"
									style={{ color: TEXT }}
								>
									{hasRows ? fmtVol(avgVolume) : '—'}
								</p>
							)}
							<p className="mt-1 text-sm" style={{ color: MUTED }}>
								Avg. daily volume
							</p>
						</div>
					</div>

					{/* Price chart */}
					<div className="mb-8">
						<div className="mb-2 flex items-baseline justify-between">
							<h2 className="text-sm font-semibold" style={{ color: TEXT }}>
								Closing price, daily
							</h2>
							<span className="text-xs" style={{ color: MUTED }}>
								{hasRows
									? `${fmtUsd(minClose)} – ${fmtUsd(maxClose)}`
									: ''}
							</span>
						</div>
						{loading ? (
							<ChartSkeleton height={240} />
						) : (
							<ResponsiveContainer width="100%" height={240}>
								<AreaChart data={priceChartData}>
									<defs>
										<linearGradient
											id="closeFill"
											x1="0"
											y1="0"
											x2="0"
											y2="1"
										>
											<stop
												offset="0%"
												stopColor={PRIMARY}
												stopOpacity={0.22}
											/>
											<stop
												offset="100%"
												stopColor={PRIMARY}
												stopOpacity={0}
											/>
										</linearGradient>
									</defs>
									<CartesianGrid
										strokeDasharray="3 3"
										stroke="#eee"
										vertical={false}
									/>
									<XAxis
										dataKey="date"
										fontSize={11}
										tick={{ fill: MUTED }}
										minTickGap={40}
									/>
									<YAxis
										domain={['auto', 'auto']}
										tickFormatter={(v) => `$${Number(v).toFixed(0)}`}
										fontSize={11}
										tick={{ fill: MUTED }}
										width={48}
									/>
									<Tooltip
										formatter={(v: number) => fmtUsd(Number(v))}
										labelStyle={{ color: TEXT }}
									/>
									<Area
										type="linear"
										dataKey="close"
										stroke={PRIMARY}
										strokeWidth={2}
										fill="url(#closeFill)"
										dot={false}
									/>
								</AreaChart>
							</ResponsiveContainer>
						)}
					</div>

					{/* Volume chart */}
					<div className="mb-8">
						<div className="mb-2 flex items-baseline justify-between">
							<h2 className="text-sm font-semibold" style={{ color: TEXT }}>
								Shares traded, daily
							</h2>
							<span className="text-xs" style={{ color: MUTED }}>
								{hasRows && peakVolumeDay
									? `avg ${fmtVol(avgVolume)} · peak ${fmtVol(peakVolumeDay.volume)}`
									: ''}
							</span>
						</div>
						{loading ? (
							<ChartSkeleton height={180} />
						) : (
							<ResponsiveContainer width="100%" height={180}>
								<BarChart data={volumeChartData}>
									<CartesianGrid
										strokeDasharray="3 3"
										stroke="#eee"
										vertical={false}
									/>
									<XAxis
										dataKey="date"
										fontSize={11}
										tick={{ fill: MUTED }}
										minTickGap={40}
									/>
									<YAxis
										tickFormatter={(v) => fmtVol(Number(v))}
										fontSize={11}
										tick={{ fill: MUTED }}
										width={48}
									/>
									<Tooltip
										formatter={(v: number) => fmtVol(Number(v))}
										labelStyle={{ color: TEXT }}
									/>
									<Bar dataKey="volume" fill="#e18727" radius={[2, 2, 0, 0]} />
								</BarChart>
							</ResponsiveContainer>
						)}
					</div>

					{/* Observations */}
					<div>
						<h2
							className="mb-2 text-sm font-semibold"
							style={{ color: TEXT }}
						>
							Observations
						</h2>
						{loading ? (
							<div className="animate-pulse space-y-2">
								<div className="h-4 w-3/4 rounded bg-gray-200" />
								<div className="h-4 w-1/2 rounded bg-gray-200" />
							</div>
						) : (
							<ul
								className="list-disc space-y-1 pl-5 text-sm"
								style={{ color: MUTED }}
							>
								<li>
									{rows.length} trading sessions from{' '}
									{first ? fmtDateShort(first.date) : '—'} to{' '}
									{last ? fmtDateShort(last.date) : '—'}.
								</li>
								{bestDay && (
									<li>
										Best single-day return:{' '}
										<span style={{ color: POSITIVE }}>
											{fmtPct(bestDay.return_pct)}
										</span>{' '}
										on {fmtDateShort(bestDay.date)}.
									</li>
								)}
								{worstDay && (
									<li>
										Worst single-day return:{' '}
										<span style={{ color: NEGATIVE }}>
											{fmtPct(worstDay.return_pct)}
										</span>{' '}
										on {fmtDateShort(worstDay.date)}.
									</li>
								)}
								{peakVolumeDay && (
									<li>
										Peak volume: {fmtVol(peakVolumeDay.volume)} on{' '}
										{fmtDateShort(peakVolumeDay.date)}.
									</li>
								)}
							</ul>
						)}
					</div>
				</>
			)}
		</main>
	);
}
