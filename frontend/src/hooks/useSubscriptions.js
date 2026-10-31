import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '@/lib/api';
export const subscriptionKeys = {
    all: ['subscriptions'],
    list: () => [...subscriptionKeys.all, 'list'],
    detail: (id) => [...subscriptionKeys.all, 'detail', id],
};
export function useSubscriptions() {
    return useQuery({
        queryKey: subscriptionKeys.list(),
        queryFn: () => api.subscriptions.list(),
    });
}
export function useSubscription(id) {
    return useQuery({
        queryKey: subscriptionKeys.detail(id),
        queryFn: () => api.subscriptions.get(id),
        enabled: id > 0,
    });
}
export function useCreateSubscription() {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (data) => api.subscriptions.create(data),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: subscriptionKeys.list() });
        },
    });
}
export function useUpdateSubscription(id) {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: (data) => api.subscriptions.update(id, data),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: subscriptionKeys.detail(id) });
            qc.invalidateQueries({ queryKey: subscriptionKeys.list() });
        },
    });
}
export function useDeleteSubscription(id) {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: () => api.subscriptions.delete(id),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: subscriptionKeys.list() });
        },
    });
}
export function useScanSubscription(id) {
    const qc = useQueryClient();
    return useMutation({
        mutationFn: () => api.subscriptions.scan(id),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: subscriptionKeys.detail(id) });
        },
    });
}
