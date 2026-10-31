import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '@/lib/api';
export const mediaKeys = {
    all: ['media'],
    list: () => [...mediaKeys.all, 'list'],
    listFiltered: (filters) => [...mediaKeys.list(), filters],
    detail: (id) => [...mediaKeys.all, 'detail', id],
};
export function useMedia(filters) {
    return useQuery({
        queryKey: mediaKeys.listFiltered(filters || {}),
        queryFn: () => api.media.list(filters),
    });
}
export function useMediaDetail(id) {
    return useQuery({
        queryKey: mediaKeys.detail(id),
        queryFn: () => api.media.get(id),
        enabled: id > 0,
    });
}
export function useDownloadMedia(id) {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: () => api.media.download(id),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: mediaKeys.detail(id) });
        },
    });
}
export function useRequeueMedia(id) {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: () => api.media.requeue(id),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: mediaKeys.detail(id) });
        },
    });
}
