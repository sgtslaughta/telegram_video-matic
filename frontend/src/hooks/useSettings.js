import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '@/lib/api';
export const settingKeys = {
    all: () => ['settings'],
};
export function useSettings() {
    return useQuery({
        queryKey: settingKeys.all(),
        queryFn: () => api.settings.get(),
        staleTime: Infinity,
    });
}
export function useUpdateSettings() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (data) => api.settings.update(data),
        onSuccess: (data) => {
            qc.setQueryData(settingKeys.all(), data);
        },
    });
}
