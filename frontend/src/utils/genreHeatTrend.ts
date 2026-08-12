import type { EChartsOption } from 'echarts'
import type { GenrePositioningTimeline, GenrePositioningTimelinePoint } from '../types/genrePositioning'

export type ChartDatum = { value: number; raw: GenrePositioningTimelinePoint }

export function buildGenreHeatTrendOption(timeline: GenrePositioningTimeline): EChartsOption {
  const genres = new Map<string, { name: string; color: string; points: Map<string, GenrePositioningTimelinePoint> }>()
  for (const point of timeline.points) {
    const genre = genres.get(point.genre_module_id) || {
      name: point.genre_name,
      color: point.theme_color,
      points: new Map<string, GenrePositioningTimelinePoint>(),
    }
    genre.points.set(point.period, point)
    genres.set(point.genre_module_id, genre)
  }
  const series = [...genres.values()]
    .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
    .map((genre) => ({
      name: genre.name,
      type: 'line' as const,
      smooth: true,
      symbol: 'circle',
      symbolSize: 10,
      showSymbol: true,
      connectNulls: false,
      emphasis: { focus: 'series' as const },
      endLabel: { show: true, formatter: '{a}', distance: 12, color: genre.color, fontSize: 12 },
      lineStyle: { width: 3, color: genre.color },
      itemStyle: { color: genre.color, borderColor: '#ffffff', borderWidth: 2 },
      data: timeline.periods.map((period): ChartDatum | null => {
        const point = genre.points.get(period)
        return point ? { value: point.average_heat, raw: point } : null
      }),
    }))

  return {
    animationDuration: 480,
    color: [...genres.values()].map((genre) => genre.color),
    grid: { left: 62, right: 150, top: 56, bottom: timeline.periods.length > 12 ? 92 : 58, containLabel: true },
    legend: { type: 'scroll', top: 8, textStyle: { color: '#8fa0b8', fontSize: 11 } },
    toolbox: { right: 12, top: 8, feature: { saveAsImage: { title: '保存图表' } } },
    tooltip: {
      trigger: 'item',
      renderMode: 'richText',
      backgroundColor: '#111a2d',
      borderColor: '#334155',
      textStyle: { color: '#eef2f8', fontSize: 12, lineHeight: 20 },
      formatter: (params: unknown) => {
        const payload = params as { data?: ChartDatum }
        const point = payload.data?.raw
        if (!point) return ''
        return [
          `平台：${timeline.upload_platform}`,
          `题材：${point.genre_name}`,
          `月份：${point.period}`,
          `平均热度：${point.average_heat}`,
          `素材数量：${point.material_count}`,
        ].join('\n')
      },
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timeline.periods,
      axisLabel: { color: '#8fa0b8', fontSize: 11, margin: 16 },
      axisLine: { lineStyle: { color: '#43506a' } },
      splitLine: { show: true, lineStyle: { color: 'rgba(100,116,139,.16)' } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      name: '平均热度',
      nameTextStyle: { color: '#8fa0b8', padding: [0, 0, 8, 0] },
      axisLabel: { color: '#8fa0b8', formatter: '{value}' },
      axisLine: { show: true, lineStyle: { color: '#43506a' } },
      splitLine: { lineStyle: { color: 'rgba(100,116,139,.16)' } },
    },
    dataZoom: timeline.periods.length > 12
      ? [
          { type: 'inside', xAxisIndex: 0, startValue: Math.max(0, timeline.periods.length - 12), endValue: timeline.periods.length - 1 },
          { type: 'slider', xAxisIndex: 0, height: 20, bottom: 20, startValue: Math.max(0, timeline.periods.length - 12), endValue: timeline.periods.length - 1 },
        ]
      : [],
    series,
  }
}

