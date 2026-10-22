import { Card, Statistic } from "antd";

type Props = {
  title: string;
  value: number | string;
  suffix?: string;
};

export default function StatCard({ title, value, suffix }: Props) {
  return (
    <Card className="shadow-sm">
      <Statistic title={title} value={value} suffix={suffix} />
    </Card>
  );
}
