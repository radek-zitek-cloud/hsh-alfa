import { useQuery } from '@tanstack/react-query';
import { widgetsApi } from '../services/api';

export const useWidget = (widgetId, options = {}) => {
  return useQuery({
    queryKey: ['widget', widgetId],
    queryFn: async () => {
      const response = await widgetsApi.getData(widgetId, options.forceRefresh);
      return response.data;
    },
    refetchInterval: options.refetchInterval || 60000, // Default: 1 minute
    enabled: !!widgetId,
    ...options,
  });
};

export const useWidgets = () => {
  return useQuery({
    queryKey: ['widgets'],
    queryFn: async () => {
      const response = await widgetsApi.getAll();
      return response.data.widgets;
    },
  });
};

export const useBookmarks = (category = null) => {
  return useQuery({
    queryKey: ['bookmarks', category],
    queryFn: async () => {
      const response = await bookmarksApi.getAll(category);
      return response.data;
    },
  });
};
