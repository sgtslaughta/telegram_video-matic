import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '@/lib/api';
export const pluginKeys = {
    all: () => ['plugins'],
};
export function usePlugins() {
    return useQuery({
        queryKey: pluginKeys.all(),
        queryFn: () => api.plugins.list(),
        staleTime: Infinity,
    });
}
export function useUpdatePlugin() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (data) => api.plugins.update(data.name, data.config),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: pluginKeys.all() });
        },
    });
}
