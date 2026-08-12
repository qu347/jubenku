import { request } from './http'
import type { GenrePositioningList, GenrePositioningTimeline } from '../types/genrePositioning'

export const listGenrePositioning = () =>
  request<GenrePositioningList>({ method: 'GET', url: '/genre-positioning' })

export const getGenrePositioningTimeline = (uploadPlatform: string) =>
  request<GenrePositioningTimeline>({
    method: 'GET',
    url: '/genre-positioning/timeline',
    params: { upload_platform: uploadPlatform },
  })

