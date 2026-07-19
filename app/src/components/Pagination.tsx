import { useEffect, useState, type FormEvent } from 'react'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface PaginationProps {
  page: number
  total: number
  pageSize: number
  disabled?: boolean
  pageSizeOptions?: number[]
  onChange: (page: number) => void
  onPageSizeChange?: (pageSize: number) => void
}

const getVisiblePages = (page: number, totalPages: number) => {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, index) => index + 1)
  if (page <= 4) return [1, 2, 3, 4, 5, 'end-ellipsis', totalPages] as const
  if (page >= totalPages - 3) {
    return [1, 'start-ellipsis', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages] as const
  }
  return [1, 'start-ellipsis', page - 1, page, page + 1, 'end-ellipsis', totalPages] as const
}

export default function Pagination({
  page,
  total,
  pageSize,
  disabled = false,
  pageSizeOptions = [10, 20, 50, 100],
  onChange,
  onPageSizeChange,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const currentPage = Math.min(Math.max(page, 1), totalPages)
  const [jumpPage, setJumpPage] = useState(String(currentPage))

  useEffect(() => {
    setJumpPage(String(currentPage))
  }, [currentPage])

  useEffect(() => {
    if (total > 0 && page !== currentPage) onChange(currentPage)
  }, [currentPage, onChange, page, total])

  if (total === 0) return null

  const start = (currentPage - 1) * pageSize + 1
  const end = Math.min(currentPage * pageSize, total)
  const changePage = (nextPage: number) => {
    const normalized = Math.min(Math.max(nextPage, 1), totalPages)
    if (normalized !== currentPage) onChange(normalized)
  }
  const handleJump = (event: FormEvent) => {
    event.preventDefault()
    const parsed = Number.parseInt(jumpPage, 10)
    const normalized = Number.isFinite(parsed) ? Math.min(Math.max(parsed, 1), totalPages) : currentPage
    setJumpPage(String(normalized))
    changePage(normalized)
  }

  return (
    <div className="mt-4 flex flex-col gap-3 border-t pt-4 xl:flex-row xl:items-center xl:justify-between">
      <p className="text-sm text-muted-foreground">
        共 <span className="font-medium text-foreground">{total}</span> 条，当前显示 {start}-{end} 条
      </p>

      <div className="flex flex-wrap items-center gap-3">
        {onPageSizeChange && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>每页</span>
            <Select
              disabled={disabled}
              onValueChange={(value) => onPageSizeChange(Number(value))}
              value={String(pageSize)}
            >
              <SelectTrigger aria-label="每页条数" className="w-20" size="sm"><SelectValue /></SelectTrigger>
              <SelectContent>
                {pageSizeOptions.map((option) => <SelectItem key={option} value={String(option)}>{option}</SelectItem>)}
              </SelectContent>
            </Select>
            <span>条</span>
          </div>
        )}

        <nav aria-label="分页导航" className="flex items-center gap-1">
          <Button aria-label="第一页" disabled={disabled || currentPage <= 1} onClick={() => changePage(1)} size="icon-sm" title="第一页" variant="outline"><ChevronsLeft className="h-4 w-4" /></Button>
          <Button aria-label="上一页" disabled={disabled || currentPage <= 1} onClick={() => changePage(currentPage - 1)} size="icon-sm" title="上一页" variant="outline"><ChevronLeft className="h-4 w-4" /></Button>
          <div className="hidden items-center gap-1 sm:flex">
            {getVisiblePages(currentPage, totalPages).map((item) =>
              typeof item === 'string' ? (
                <span className="flex h-8 w-8 items-center justify-center text-sm text-muted-foreground" key={item}>...</span>
              ) : (
                <Button
                  aria-current={item === currentPage ? 'page' : undefined}
                  className="h-8 w-8 p-0"
                  disabled={disabled}
                  key={item}
                  onClick={() => changePage(item)}
                  variant={item === currentPage ? 'default' : 'outline'}
                >
                  {item}
                </Button>
              ),
            )}
          </div>
          <span className="min-w-20 text-center text-sm text-muted-foreground sm:hidden">{currentPage} / {totalPages}</span>
          <Button aria-label="下一页" disabled={disabled || currentPage >= totalPages} onClick={() => changePage(currentPage + 1)} size="icon-sm" title="下一页" variant="outline"><ChevronRight className="h-4 w-4" /></Button>
          <Button aria-label="最后一页" disabled={disabled || currentPage >= totalPages} onClick={() => changePage(totalPages)} size="icon-sm" title="最后一页" variant="outline"><ChevronsRight className="h-4 w-4" /></Button>
        </nav>

        <form className="flex items-center gap-2" onSubmit={handleJump}>
          <span className="text-sm text-muted-foreground">跳至</span>
          <Input
            aria-label="跳转页码"
            className="h-8 w-16 px-2 text-center"
            disabled={disabled}
            max={totalPages}
            min={1}
            onChange={(event) => setJumpPage(event.target.value)}
            type="number"
            value={jumpPage}
          />
          <Button disabled={disabled} size="sm" type="submit" variant="outline">确定</Button>
        </form>
      </div>
    </div>
  )
}
