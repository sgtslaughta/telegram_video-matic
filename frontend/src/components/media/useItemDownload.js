import { useQueryClient } from '@tanstack/react-query';
import { useDownloadMedia } from '@/hooks/useMedia';
import { withToast } from '@/lib/toast';
import * as api from '@/lib/api';
/** Download an item: known media rows go through the media API, others via browseDownload. */
export function useItemDownload(item, channelId) {
    const qc = useQueryClient();
    const dl = useDownloadMedia(item.media_id ?? 0);
    const run = () => withToast(async () => {
        if (item.media_id)
            await dl.mutateAsync();
        else
            await api.channels.browseDownload(channelId, item.tg_msg_id);
        qc.invalidateQueries({ queryKey: ['browse'] });
    }, { success: 'Download queued', error: 'Could not queue the download' });
    return { onDownload: run, pending: dl.isPending };
}
