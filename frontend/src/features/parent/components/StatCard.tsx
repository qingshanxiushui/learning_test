import { Card, Statistic } from "antd";
import type { ReactNode } from "react";

type Props = {
  title: string;
  value: number | string;
  suffix?: string;
  icon?: ReactNode;
  accent?: string;
  hint?: string;
};

export default function StatCard({
  title,
  value,
  suffix,
  icon,
  accent = "#24665c",
  hint,
}: Props) {
  return (
    <Card className="parent-stat-card">
      <div className="parent-stat-head">
        <span className="parent-stat-title">{title}</span>
        {icon && (
          <span
            className="parent-stat-icon"
            style={{ color: accent, background: `${accent}14` }}
            aria-hidden="true"
          >
            {icon}
          </span>
        )}
      </div>
      <Statistic value={value} suffix={suffix} />
      {hint && <div className="parent-stat-hint">{hint}</div>}
    </Card>
  );
}
